"""News sentiment executor using deterministic labels and source item evidence."""

from collections.abc import Sequence

from src.executors.calculations import rounded
from src.executors.context import RunContext
from src.executors.contracts import ExecutorResult, SentimentData
from src.executors.runner import ExecutorRunner
from src.schemas.common import EvidenceItem, Signal
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, SignalDirection, SourceType
from src.schemas.request import NormalizedRequest


def calculate_sentiment(scores: Sequence[float]) -> dict[str, float | int | str | None]:
    """Classify normalized MCP article scores without an LLM sentiment guess."""

    if not scores:
        return {
            "sentiment_score": None,
            "sentiment_label": "unavailable",
            "positive_items": 0,
            "neutral_items": 0,
            "negative_items": 0,
        }
    score = sum(scores) / len(scores)
    positive = sum(value > 0.1 for value in scores)
    negative = sum(value < -0.1 for value in scores)
    neutral = len(scores) - positive - negative
    label = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
    return {
        "sentiment_score": rounded(score),
        "sentiment_label": label,
        "positive_items": positive,
        "neutral_items": neutral,
        "negative_items": negative,
    }


class SentimentExecutor:
    """Summarize supplied news labels, headlines, topics, and downside narratives."""

    domain = AnalysisDomain.SENTIMENT
    agent_name = "sentiment_executor"

    def __init__(self, runner: ExecutorRunner | None = None) -> None:
        self._runner = runner or ExecutorRunner()

    async def execute(
        self, run_context: RunContext, ticker: str, normalized_request: NormalizedRequest
    ) -> DomainOutcome:
        normalized_ticker = ticker.strip().upper()
        return await self._runner.run(
            run_context=run_context,
            ticker=normalized_ticker,
            request=normalized_request,
            domain=self.domain,
            agent=self.agent_name,
            operation="sentiment_analysis",
            worker=lambda: self._analyze(run_context, normalized_ticker),
        )

    async def _analyze(self, run_context: RunContext, ticker: str) -> ExecutorResult:
        response = await run_context.mcp_client.get_news(ticker, run_id=run_context.run_id)
        calculation = calculate_sentiment([article.sentiment_score for article in response.articles])
        topics = list(dict.fromkeys(topic for article in response.articles for topic in article.topics))
        narratives = [article.headline for article in response.articles]
        unavailable = (
            {"sentiment_score": "The MCP news response contained no article-level sentiment scores."}
            if not response.articles
            else {}
        )
        data = SentimentData(
            narratives=narratives,
            topics=topics,
            unavailable=unavailable,
            **calculation,
        )
        evidence = [
            EvidenceItem(
                evidence_id=f"mock:{ticker}:news:{index}:{article.published_at.date().isoformat()}",
                title=article.headline,
                source="finance_mcp.get_news",
                source_type=SourceType.MOCK,
                observed_at=article.published_at,
                details={"sentiment_score": article.sentiment_score, "topics": article.topics},
            )
            for index, article in enumerate(response.articles, start=1)
        ]
        if not evidence:
            evidence.append(
                EvidenceItem(
                    evidence_id=f"mock:{ticker}:news:{response.as_of.date().isoformat()}",
                    title=f"{ticker} news response",
                    source="finance_mcp.get_news",
                    source_type=SourceType.MOCK,
                    observed_at=response.as_of,
                    details={"article_count": 0},
                )
            )

        opportunities, risks = self._opportunities_and_risks(data)
        result = ExecutorResult(
            summary=self._summary(ticker, data),
            signals=self._signals(data),
            opportunities=opportunities,
            risks=risks,
            evidence=evidence,
            data=data.model_dump(mode="json"),
        )
        return await self._interpret_if_configured(run_context, ticker, result)

    @staticmethod
    def _summary(ticker: str, data: SentimentData) -> str:
        if data.sentiment_score is None:
            return f"{ticker} has no article-level sentiment evidence in the supplied mock news response."
        return (
            f"{ticker} news sentiment is {data.sentiment_label} at {data.sentiment_score} "
            f"across {data.positive_items + data.neutral_items + data.negative_items} supplied articles."
        )

    @staticmethod
    def _signals(data: SentimentData) -> list[Signal]:
        if data.sentiment_score is None:
            return []
        return [
            Signal(
                name="News sentiment",
                direction={
                    "positive": SignalDirection.POSITIVE,
                    "negative": SignalDirection.NEGATIVE,
                }.get(data.sentiment_label, SignalDirection.NEUTRAL),
                value=data.sentiment_score,
                unit="normalized_-1_to_1",
                rationale="The score is the mean of supplied article sentiment scores; labels use +/-0.1 thresholds.",
            )
        ]

    @staticmethod
    def _opportunities_and_risks(data: SentimentData) -> tuple[list[str], list[str]]:
        opportunities: list[str] = []
        risks: list[str] = []
        if data.positive_items > data.negative_items:
            opportunities.append("Positive supplied news items outnumber negative supplied news items.")
        if data.negative_items:
            risks.append(f"{data.negative_items} supplied news item(s) carry negative sentiment.")
        if data.unavailable:
            risks.extend("Unavailable: " + reason for reason in data.unavailable.values())
        return opportunities, risks

    async def _interpret_if_configured(
        self, run_context: RunContext, ticker: str, result: ExecutorResult
    ) -> ExecutorResult:
        if run_context.interpreter is None:
            return result
        interpretation = await run_context.interpreter.interpret(
            domain=self.domain.value,
            ticker=ticker,
            facts=result.data,
            evidence_ids=[item.evidence_id for item in result.evidence],
        )
        return result.model_copy(
            update={
                "summary": interpretation.summary,
                "opportunities": interpretation.opportunities,
                "risks": interpretation.risks,
                "evidence": [
                    *result.evidence,
                    self._runner.model_evidence(
                        run_context=run_context,
                        agent=self.agent_name,
                        cited_evidence_ids=interpretation.evidence_ids,
                    ),
                ],
            }
        )
