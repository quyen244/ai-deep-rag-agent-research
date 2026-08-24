```mermaid
flowchart TB
    subgraph INPUT["🟢 INPUT LAYER"]
        Q["📝 User Query<br>'Phân tích AAPL và TSLA'"]
    end

    subgraph ORCH["🔵 ORCHESTRATION LAYER"]
        direction TB
        O["🎯 Main Orchestrator<br>(LangGraph Supervisor)"]
        O --> P1["Phân tích kỹ thuật"]
        O --> P2["Phân tích cơ bản"]
        O --> P3["Phân tích sentiment"]
        O --> P4["Phân tích vĩ mô"]
    end

    subgraph AGENTS["🟡 AGENT EXECUTION LAYER - Chạy song song"]
        direction TB
        
        subgraph TECH["Technical Agent"]
            T1["📊 Lấy OHLCV<br>1 năm - 5 năm"]
            T2["📈 Tính chỉ báo<br>RSI, MACD, BB, MA"]
            T3["🎯 Xác định<br>Xu hướng & Pattern"]
            T1 --> T2 --> T3
        end

        subgraph FUND["Fundamental Agent"]
            F1["📋 Lấy BCTC<br>Quý gần nhất"]
            F2["📊 Tính định giá<br>P/E, P/B, EV/EBITDA"]
            F3["🏢 Phân tích<br>Biên lợi nhuận, ROE"]
            F1 --> F2 --> F3
        end

        subgraph SENT["Sentiment Agent"]
            S1["📰 Crawl tin tức<br>Google News, Reuters"]
            S2["🧠 Phân tích cảm xúc<br>NLP / VADER"]
            S3["📊 Tổng hợp<br>Score sentiment"]
            S1 --> S2 --> S3
        end

        subgraph MACRO["Macro Agent"]
            M1["🌍 Lấy dữ liệu<br>GDP, CPI, Lãi suất"]
            M2["🏭 Phân tích<br>Ngành, đối thủ"]
            M3["📈 Xu hướng<br>Thị trường chung"]
            M1 --> M2 --> M3
        end
    end

    subgraph VALID["🟠 VALIDATION LAYER"]
        V["🔍 Validator Agent<br>Kiểm tra tính đầy đủ"]
        V -->|"Thiếu dữ liệu"| LOOP["🔄 Yêu cầu thu thập bổ sung"]
        LOOP --> AGENTS
        V -->|"Đủ dữ liệu"| SYNTH
    end

    subgraph SYNTH["🟣 SYNTHESIS LAYER"]
        SYN["📝 Synthesizer Agent<br>Tổng hợp báo cáo"]
        SYN --> R1["📄 Tóm tắt điều hành"]
        SYN --> R2["📊 Bảng so sánh<br>AAPL vs TSLA"]
        SYN --> R3["⚠️ Rủi ro & Cơ hội"]
        SYN --> R4["🔗 Trích dẫn nguồn"]
    end

    subgraph OUTPUT["🔴 OUTPUT LAYER"]
        O1["📑 Báo cáo phân tích<br>có trích dẫn"]
        O2["⚠️ Disclaimer<br>Không phải lời khuyên đầu tư"]
    end

    Q --> O
    O --> P1 & P2 & P3 & P4
    
    P1 --> TECH
    P2 --> FUND
    P3 --> SENT
    P4 --> MACRO
    
    TECH --> V
    FUND --> V
    SENT --> V
    MACRO --> V
    
    SYNTH --> R1 & R2 & R3 & R4
    R1 & R2 & R3 & R4 --> O1
    O1 --> O2

    %% Styling
    classDef input fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef orche fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef agent fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef valid fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef synth fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef output fill:#ffebee,stroke:#c62828,stroke-width:2px
    
    class Q input
    class O orche
    class TECH,FUND,SENT,MACRO agent
    class V,LOOP valid
    class SYN,R1,R2,R3,R4 synth
    class O1,O2 output
```

🔍 Giải thích chi tiết từng bước
1️⃣ Input Layer - Nhận yêu cầu
User nhập câu hỏi, ví dụ: "Phân tích cổ phiếu Apple và Tesla, so sánh hiệu quả kinh doanh"

Orchestrator parse câu hỏi, trích xuất: Mã cổ phiếu (AAPL, TSLA), Khung thời gian (1 năm, 5 năm), Loại phân tích (kỹ thuật, cơ bản, cảm xúc)

2️⃣ Orchestration Layer - Điều phối tác vụ
Orchestrator chia nhỏ nhiệm vụ thành các subtask:

Phân tích kỹ thuật → Giao cho Technical Agent

Phân tích cơ bản → Giao cho Fundamental Agent

Phân tích sentiment → Giao cho Sentiment Agent

Phân tích vĩ mô → Giao cho Macro Agent

Tất cả Agent được kích hoạt song song để tiết kiệm thời gian

3️⃣ Agent Execution Layer - Các Agent chuyên biệt hoạt động
Technical Agent (Phân tích kỹ thuật)

Gọi MCP Server (Infoway/Yahoo Finance) → Lấy dữ liệu OHLCV (giá mở, cao, thấp, đóng, khối lượng)

Tính toán chỉ báo: RSI, MACD, Bollinger Bands, Moving Averages

Xác định: Xu hướng (tăng/giảm), vùng kháng cự/hỗ trợ, breakout/consolidation

Fundamental Agent (Phân tích cơ bản)

Gọi MCP Server (SEC EDGAR, Infoway) → Lấy báo cáo tài chính (income statement, balance sheet, cash flow)

Tính toán chỉ số định giá: P/E, P/B, EV/EBITDA, biên lợi nhuận, ROE, ROA

So sánh với trung bình ngành

Sentiment Agent (Phân tích cảm xúc)

Crawl tin tức từ Google News, Reuters, Bloomberg

Dùng NLP (VADER, BERT fine-tuned) để phân tích cảm xúc (positive/negative/neutral)

Tổng hợp sentiment score và xu hướng tin tức

Macro Agent (Phân tích vĩ mô)

Thu thập dữ liệu kinh tế vĩ mô: GDP, CPI, lãi suất, tỷ giá

Phân tích ngành và đối thủ cạnh tranh

Đánh giá ảnh hưởng của yếu tố vĩ mô đến cổ phiếu

4️⃣ Validation Layer - Kiểm tra chất lượng
Validator Agent kiểm tra:

Dữ liệu đã đầy đủ chưa? (Thiếu OHLCV? Thiếu chỉ số định giá?)

Có mâu thuẫn giữa các nguồn không?

Có lỗ hổng logic trong phân tích không?

Nếu thiếu dữ liệu: Quay lại Agent Execution Layer để thu thập bổ sung

Nếu đủ: Chuyển sang Synthesis Layer

5️⃣ Synthesis Layer - Tổng hợp báo cáo
Synthesizer Agent tổng hợp tất cả đầu ra thành báo cáo có cấu trúc:

Tóm tắt điều hành (Executive Summary): Điểm chính, khuyến nghị chung (không phải lời khuyên đầu tư)

Bảng so sánh: AAPL vs TSLA - Kỹ thuật, Cơ bản, Sentiment

Rủi ro & Cơ hội: Điểm mạnh, điểm yếu, cơ hội, rủi ro

Trích dẫn nguồn: Mọi số liệu đều có link/dẫn chứng

6️⃣ Output Layer - Trả về kết quả
Báo cáo phân tích chi tiết

Disclaimer: "Đây là phân tích dữ liệu, không phải lời khuyên đầu tư" - Rất quan trọng để tránh rủi ro pháp lý

💡 Điểm nổi bật của hệ thống này
Song song hóa: 4 Agent phân tích cùng lúc → Tối ưu thời gian

Validation: Kiểm tra chất lượng tự động → Đảm bảo độ chính xác

Tích hợp MCP: Dễ dàng thêm nguồn dữ liệu mới

Trích dẫn nguồn: Minh bạch, giảm ảo giác

Disclaimer: Bảo vệ pháp lý