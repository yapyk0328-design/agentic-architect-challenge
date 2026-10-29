# Part 1: System Design and Critical Thinking

## 1. Overview

This design proposes an agentic system for processing customer-support emails through a controlled and evidence-based workflow. When an email is received, the system first validates and normalizes its content, retrieves the customer’s recent contact history, and checks for critical conditions. Emails involving data loss, service outages, security breaches, or more than three support contacts within seven days are immediately routed to a human agent before any response is drafted.

If no critical condition is detected, the system classifies the email into an appropriate category, such as Billing, Technical, or Feedback. It then selects the relevant internal knowledge base and retrieves supporting information from approved PDFs or FAQs. If sufficient evidence cannot be found, the email is escalated to a human agent instead of allowing the language model to generate an unsupported answer.

For requests with sufficient evidence, the system determines whether the email is related to a refund. Normal requests are drafted using the retrieved knowledge-base evidence. Refund-related requests require an additional check to confirm that valid information is available from an approved refund-policy document. If valid refund evidence is unavailable, the request is routed to a human agent. Otherwise, the system drafts the response using only the approved refund policy. All generated responses are validated before being returned as drafts, helping ensure that the system does not introduce unsupported facts or hallucinate company policies.

## 2. Requirements

The system must:

1. Classify emails into supported categories such as Billing, Technical, Feedback, Account, Refund, and Other.
2. Draft responses using information retrieved from approved internal PDFs and FAQs.
3. Route an email to a human agent before drafting when:
   - the email mentions or implies data loss;
   - the email mentions or implies a service outage;
   - the email mentions or implies a security breach; or
   - the customer has contacted support more than three times within the last seven days.
4. Prevent unsupported statements about the company's refund policy.


## 3. Component Explanation

### 3.1 Receive Customer Email

The workflow begins when an email is received through an email provider, support portal, or ticketing platform. Each request is assigned a unique email ID and linked to a customer ID so that the system can retrieve the correct customer history and maintain an audit trail.

A normalized input object may contain:

```json
{
  "email_id": "email-001",
  "customer_id": "customer-123",
  "subject": "Duplicate subscription charge",
  "body": "I was charged twice. Can I receive a refund?",
  "received_at": "2026-10-28T10:00:00Z"
}
```

### 3.2 Validate and Normalize Email

The system validates that all required fields are present and that the message can be processed safely. It also detects duplicate messages, enforces input-size limits, and identifies unsupported attachments.

Normalization converts HTML into plain text and removes signatures, quoted reply chains, and unnecessary formatting. The original email is retained for auditing, while the normalized version is used by downstream components.

### 3.3 Load Customer Contact History

The system retrieves the customer's previous support activity from the customer-support database. It calculates the number of contacts made by the same customer within the previous seven days.

This value must come from the support database rather than from the language model. The escalation rule is strictly `contact_count_7d > 3`, meaning that the fourth contact within seven days triggers human escalation.

### 3.4 Critical Issue Guard

Before classification, retrieval, or response drafting, the Critical Issue Guard evaluates whether the message contains a high-risk condition. The minimum deterministic rules check for data loss, service outage, and security breach indicators, as well as the seven-day contact count.

Keyword rules are fast and auditable, but customers may describe a problem indirectly. For example, "all of my files disappeared" may indicate data loss without using that exact phrase. Therefore, a semantic classifier may be used as an additional detector. It must not replace the deterministic rules.

If any escalation condition is met, the email bypasses all automated drafting nodes.

### 3.5 Route Email to a Human Agent

Critical requests are placed in the appropriate human-support queue. Data-loss and outage cases may be assigned to senior technical support, while suspected security breaches may be routed to a security-response team.

The system records the email ID, customer ID, priority, escalation reason, timestamp, and rule that triggered the decision. Automated drafting is then stopped. A pre-approved acknowledgement template may be sent, but the language model must not generate a technical or policy answer for the critical request.

3.6 Classify Email Categories
If no critical condition is detected, the system classifies the email into one or more supported categories. The classifier returns structured output rather than unrestricted text.

Example:
{
  "primary_category": "technical",
  "secondary_categories": [
    "billing",
    "refund"
  ],
  "category_confidences": {
    "technical": 0.94,
    "billing": 0.86,
    "refund": 0.81
  },
  "is_refund_related": true
}

The category with the highest confidence score is selected as the primary category and determines the main routing destination and knowledge-base search scope. Other categories that exceed a configured confidence threshold may be included as secondary categories, with a configurable maximum to prevent the retrieval scope from becoming too broad.

Secondary categories capture additional topics within the same email. They are used to expand the knowledge-base search and activate category-specific guardrails. For example, a Billing or Technical email that also contains a refund request must still trigger the approved refund-policy evidence check.

Refund detection is maintained as a separate is_refund_related flag so that the refund-policy guardrail is not skipped when Refund is not among the highest-ranked categories. Invalid categories, low-confidence classifications, or ambiguous results are routed for human review.

### 3.7 Select the Relevant Knowledge Base

The classification result narrows the knowledge-base search scope. For example:

| Category  | Preferred knowledge sources                                 |
| --------- | ----------------------------------------------------------- |
| Billing   | Billing FAQ, Payment Guide, approved Refund Policy          |
| Technical | Troubleshooting Guide, Technical FAQ, service documentation |
| Feedback  | Feedback Handling Guide, Product FAQ                        |
| Account   | Account Policy, Authentication FAQ                          |
| Refund    | Current approved Refund Policy                              |

This mapping is implemented through document metadata instead of assuming that every category has exactly one fixed PDF.

### 3.8 Retrieve Relevant PDF or FAQ Sections

Approved PDFs and FAQs are extracted, divided into smaller chunks, and indexed with metadata such as document ID, version, category, section, page number, and approval status. A retrieval component searches the selected documents and returns the sections most relevant to the customer's question.

### 3.9 Check Evidence Sufficiency

Before drafting, the system checks whether the retrieved evidence is relevant and reliable enough to answer the request. The check considers whether evidence exists, whether it comes from an approved and current source, and whether its retrieval score exceeds a configured threshold.

If sufficient evidence is unavailable, the system routes the request to a human agent. The model is not allowed to answer from general knowledge or assumptions.

### 3.10 Refund Policy Guardrail

Refund-related requests receive an additional policy-specific check. Before generating a refund response, the system must confirm that the retrieved evidence comes from the current approved refund-policy document.

General billing FAQs, outdated policies, and model knowledge are not accepted as authoritative refund evidence. If an approved source cannot confirm the requested eligibility condition, deadline, amount, or processing rule, the request is escalated to a human agent.

This creates two refund safeguards:

1. **Pre-generation guard:** a refund response cannot be drafted without approved refund-policy evidence.
2. **Post-generation guard:** every refund-related statement in the draft must be supported by the retrieved evidence.

### 3.11 Draft Response

For a normal request, the language model drafts a response using only the retrieved knowledge-base evidence. For a refund request, it uses only evidence from the approved refund policy.

The drafting prompt instructs the model to:

- use only the supplied evidence;
- avoid adding unsupported facts, amounts, dates, deadlines, or eligibility conditions;
- identify the evidence used for the answer; and
- request human review when the evidence is incomplete.


### 3.12 Validate and Return the Draft

The final validation layer verifies that every cited evidence ID was provided by the retrieval component and that important claims are supported by the retrieved text. Refund-related numbers, deadlines, eligibility rules, and monetary statements receive stricter checks.

The validator also checks the response format, tone, length, and whether the workflow should have escalated the request earlier. If validation fails, the draft is rejected and the email is routed to a human agent. If validation passes, the system returns the draft for support-agent review.

## 4. Agentic Logic

The design is agentic because the workflow makes controlled decisions and follows different paths according to the current state. It does not execute the same sequence for every email.

Examples include:

- deciding whether to stop and escalate before drafting;
- selecting a knowledge-base scope based on classification;
- deciding whether the retrieved evidence is sufficient;
- applying an additional tool and policy path for refund requests; and
- rejecting an unsupported draft and handing control to a human agent.

The workflow state should store the input email, contact count, classification result, escalation decision, retrieved evidence, draft, validation status, and audit metadata.

## 5. Failure Handling

| Failure                                 | System behaviour                                                                |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| Email input is invalid                  | Reject or quarantine the request and log the validation error                   |
| Customer history service is unavailable | Retry with backoff; route to human if the contact-count rule cannot be verified |
| Classification confidence is low        | Route to human review                                                           |
| Knowledge-base retrieval returns no useful evidence | Do not draft; route to human                                        |
| Approved refund policy is unavailable   | Do not draft a refund answer; route to human                                    |
| LLM request times out                   | Retry a limited number of times, then route to human                            |
| LLM returns invalid structured output   | Validate with a schema, retry, then route to human                              |
| Draft contains unsupported claims       | Reject the draft and route to human                                             |
| Human ticketing service is unavailable  | Store the escalation in a durable retry queue and alert the operations team     |

All operations should be idempotent so that retrying the same email does not create duplicate drafts or human-support tickets.

## 6. Logging and Observability

The system should produce structured logs for each workflow transition. Sensitive customer information should be masked or excluded from logs.

Useful audit fields include:

- email ID and customer ID;
- normalized category and confidence score;
- seven-day contact count;
- escalation decision and reason;
- retrieved document and evidence IDs;
- knowledge-base and prompt versions;
- whether a draft was generated;
- validation result;
- model latency and token usage; and
- final workflow status.

Operational metrics should include escalation rate, classification accuracy, retrieval failure rate, refund-guardrail failure rate, human override rate, processing latency, model error rate, and queue depth.

## 7. Security and Privacy

The system should follow least-privilege access when reading internal documents and customer records. Sensitive information such as payment details, credentials, and personal identifiers should be removed or masked before being sent to an external model unless an approved data-processing agreement permits it.

Internal knowledge-base content should be treated as untrusted input. Retrieved documents must not be allowed to override system rules, change escalation conditions, or instruct the agent to ignore its guardrails.

## 8. Test Scenarios

| Scenario                                                 | Expected result                                                  |
| -------------------------------------------------------- | ---------------------------------------------------------------  |
| Email mentions data loss                                 | Escalate before drafting                                         |
| Email mentions a service outage                          | Escalate before drafting                                         |
| Email mentions a security breach                         | Escalate before drafting                                         |
| Customer has exactly three contacts in seven days        | Continue normal processing if no other critical condition exists |
| Customer has four contacts in seven days                 | Escalate before drafting                                         |
| Normal billing question with relevant evidence           | Generate and validate an evidence-grounded draft                 |
| Question with no relevant knowledge-base evidence        | Escalate without drafting                                        |
| Refund question with an approved policy source           | Draft using the approved policy and validate every policy claim  |
| Refund question without approved policy evidence         | Escalate without drafting a refund answer                        |
| Draft contains a refund deadline not present in evidence | Reject the draft and escalate                                    |

## 9. Trade-offs

### Deterministic Rules vs. Semantic Detection

Deterministic rules are predictable, fast, and easy to audit, but they may miss indirect descriptions. Semantic detection improves coverage but can produce false positives or false negatives. The proposed system therefore uses deterministic rules as the minimum safety layer and semantic detection as an additional signal. Uncertain high-risk cases are routed to humans.

### Retrieval Quality vs. Latency

Searching more documents and retrieving more chunks may improve recall, but it also increases latency, token usage, and the risk of irrelevant context. Category filtering and a small configurable top-k limit provide a practical balance.

### Automation vs. Safety

Automatically sending replies would reduce response time, but an incorrect policy statement could create customer and business risk. The proposed system returns a validated draft for human review, while allowing future automation only for well-tested, low-risk categories.

### Strict Evidence Requirements vs. Escalation Volume

Strict evidence thresholds reduce hallucination risk but may increase the number of requests sent to human agents. This is an intentional trade-off for policy-sensitive topics such as refunds and can be improved over time by expanding and maintaining the approved knowledge base.

## 10. Conclusion

The proposed architecture separates safety-critical decisions from probabilistic language-model behaviour. Critical issues are identified before drafting, category-aware retrieval grounds normal responses in internal documentation, and refund answers require evidence from an approved policy source. Human escalation, structured validation, logging, testing, and observability ensure that the system fails safely when information is missing or uncertain.
