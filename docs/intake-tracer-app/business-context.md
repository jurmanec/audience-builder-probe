# Business context

| Context | Business scenario | How our system represents it |
| --- | --- | --- |
| Saved segment | A lifecycle marketer is staffing next month's renewal program. The program already exists. He is not inventing the audience.<br><br>He opens the audience library and selects the saved segment "at-risk renewal." The platform loads the rule the audience team certified last year: a household that has been a customer for at least a year, is month-to-month, and has called support at least twice in the last 90 days. He does not rebuild those clauses. He clicks the segment, and the platform counts it against this morning's household table. The count comes back at 2,147. The segment stays in draft. Nothing is mailed, and no offer is attached. He pastes that count into the campaign brief so finance can see the reach, then sends the segment to his manager. Approval is a separate step. Only after that does the campaign pick up the bill-credit offer, the email and SMS channels, and the suppression list. | `run_template("at-risk renewal")` is that click. The name selects the stored predicate, the count is taken from the household file, and the result is a draft audience with the rule and the size. An unknown name is a segment that was never published: the library returns nothing, and he would have to build a new rule in the segment builder. |

## Technologies

A large telecommunications marketing organization commonly runs this work on Adobe Experience Platform and the application built on top of it.

- AEP is the foundational infrastructure: data ingestion, Experience Data Model (XDM) schemas, Identity Service, Real-Time Customer Profile, Segmentation Service, governance, data lake, etc.
- Real-Time CDP is the marketer-facing CDP application that runs on top of those AEP services. It provides the workflows for unifying profiles, building and managing audiences, and activating them to destinations.

## Sources

- **Saved segment.** [Build and Manage Audience Segments in Real-Time CDP](https://www.youtube.com/watch?v=sZQrfTird70). Adobe for Business. A marketer opens a named audience in a segment builder, which is the library in the renewal scenario.
