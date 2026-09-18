---
id: doc-17
title: AI Decision Flow
type: guide
created_date: '2026-09-14 15:06'
updated_date: '2026-09-14 15:07'
---
# AI Market Manager Workflow

The AI Market Manager module in Alliance Auth Industry (Reforged) is built from two separate processes. To clarify the decision moments, you can find a diagram and explanation of the process below.

## Decision Diagram (Sequence)

```mermaid
sequenceDiagram
    participant OS as Opportunity Scanner
    participant ML as AI Forecasting (Uvicorn)
    participant B as Basket (Database)
    participant BE as Basket Evaluator
    participant P as Production Tasks (Jobs)
    
    %% Opportunity Scan Process
    Note over OS,ML: 1. Periodic Market Scan
    OS->>OS: Loop through all Corp blueprints
    OS->>OS: Skip items already in a Basket
    OS->>ML: What is the Forecasted Velocity (expected daily sales)?
    ML-->>OS: Expected volume
    OS->>OS: Calculate profit margin (Sell Price - Build Cost)
    
    alt Margin >= Minimum AND Velocity >= Minimum
        OS->>B: Create 'MarketOpportunity' record (log)
        
        alt Basket has 'auto_add_basket = True'
            OS->>B: AUTOMATICALLY add item as a 'BasketItem' in the Basket
        end
    end
    
    %% Evaluation Process
    Note over BE,P: 2. Periodic Basket Evaluation
    BE->>B: Fetch all active BasketItems
    loop For each BasketItem
        BE->>BE: Calculate Current Stock (Corp Hangar)
        BE->>BE: Calculate In-Flight (Active Production Jobs)
        BE->>BE: Fetch Market Stock (Public ESI / Structure ESI)
        
        Note right of BE: Effective Stock = Hangar + In-Flight + Market
        
        BE->>ML: What is the ideal stock (Reorder Point / Target Stock)?
        ML-->>BE: Target Stock
        
        alt Effective Stock < Target Stock
            BE->>BE: Calculate Shortage (Target Stock - Effective Stock)
            BE->>BE: Round up based on 'Batch Size'
            BE->>P: Create Production Task (Job) for the shortage!
        else
            BE->>B: Log: "Skipped" (Stock is sufficient)
        end
    end
```

## How do Opportunities and Baskets relate?

1. **Market Opportunity:** This is a *suggestion*. It tells you: "Hey, Vargurs are very profitable in this hub right now."
2. **Basket:** This is your *intention to build*. You can manually add items to a basket (BasketItems). If you enable the `auto_add_basket` (Auto-Approve Opportunities) setting on a Basket, the Scanner will automatically add profitable items as BasketItems to that Basket.
3. **Jobs (Production Tasks):** These are **only** created by the *Basket Evaluator*. It looks purely at what is in the Baskets. An Opportunity will therefore never create a Job directly; it must always become a BasketItem first (manually or automatically).
