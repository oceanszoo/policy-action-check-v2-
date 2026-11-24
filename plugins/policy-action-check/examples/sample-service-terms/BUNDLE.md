---
name: pac-sample-service-terms
description: Check an action against sample-service-terms with no model, using the policy-action-check bundle in this folder.
---
# sample-service-terms: policy action bundle

https://example.com/sample-service-terms · format 2.0 · self-exam: passed (2026-11-24T03:10:17+00:00) · 23 terms, 24 features, 21 rules <!-- bundle data: fe1b54d44fddf27d1e4e812ebef6c29b9104d01b67a71d0c05ffdba50b03244b -->

## How to use
- Web app: open pac-reader.html and load this folder.
- Command line: `python3 pac.py --space <this folder> report "pur=illegal"`, plus `map`, `fit "<code>"`, `check`, `lookup "<words>"`.
- Codes: `key=value` tokens; `a+b` for several values on a multi-valued key; `&` = at the same time, `>` = after.

## Terms map

### General rules › Illegal activity
- **Applicable law and regulations** `c001`
  - gate: `pur` is one of `illegal`

### General rules › Critical infrastructure
- **Critical infrastructure** `c002`
  - gate: (`pur` is one of `sabotage` or `pur` is one of `infra_access`)

### General rules › Computer and network systems
- **Unauthorized computer or network compromise** `c003`
  - gate: `pur` is one of `cyber`
  - gate: `auth` is one of `n`

### General rules › Weapons
- **Weapons development or operation** `c005`
  - gate: (`pur` is one of `weapon_dev` or `pur` is one of `weapon_op`)

### General rules › Violence and hate
- **Violence, extremism or protected-trait discrimination** `c006`
  - gate: (`pur` is one of `violence` or `pur` is one of `extremism` or `pur` is one of `trait_disc`)

### General rules › Privacy
- **Sharing personal information without consent** `c007`
  - gate: `pur` is one of `data`
  - gate: `cons` is one of `n`

### General rules › Minors
- **Exploitation, grooming or abuse of a child** `c008`
  - gate: (`pur` is one of `exploitation` or `pur` is one of `grooming` or `pur` is one of `abuse`)
  - gate: `age < 18`

### General rules › Harmful conduct
- **Self-harm promotion, harassment or nonconsensual intimate imagery** `c010`
  - gate: (`pur` is one of `self_harm` or `pur` is one of `harassment` or `pur` is one of `nc_intimate`)

### General rules › False information
- **Disinformation or deceptive impersonation** `c011`
  - gate: (`pur` is one of `disinfo` or `pur` is one of `imp`)
  - **Disclosed fiction, satire or parody** `c012`
    - gate: `fic` is one of `y`

### General rules › Deceptive campaigns
- **Deceptive campaigns** `c013`
  - gate: (`pur` is one of `fake_support` or `pur` is one of `conceal_coord`)

### General rules › Elections
- **Election interference** `c014`
  - gate: (`pur` is one of `voter_deception` or `pur` is one of `suppression` or `pur` is one of `disruption`)

### General rules › Tracking and enforcement
- **Nonconsensual tracking or criminal-justice decisions** `c015`
  - gate: (`pur` is one of `track` or `pur` is one of `criminal`)
  - gate: (`cons` is one of `n` or `pur` is one of `criminal`)

### General rules › Fraud
- **Fraud, scams, spam or falsified records** `c017`
  - gate: (`pur` is one of `fraud` or `pur` is one of `scam` or `pur` is one of `spam` or `pur` is one of `false_record`)

### General rules › Service abuse
- **Platform abuse** `c018`
  - gate: (`pur` is one of `guardrail` or `pur` is one of `unauth_platform`)

### General rules › Explicit content
- **Sexually explicit output** `c019`
  - gate: `pur` is one of `explicit`

### Sensitive uses › Requirements
- **Qualified prior review** `c020`
  - gate: `area` is one of `credit`, `housing`, `listed_field`
  - require: `reviewed` is one of `y`
  - require: `changeable` is one of `y`
  - **Listed wholly favourable decisions** `c027`
    - gate: `favorable` is one of `y`
    - gate: `fav_list` is one of `y`
    - gate: `law_record` is one of `y`
- **Disclosure to an affected person** `c021`
  - gate: `area` is one of `credit`, `housing`, `listed_field`
  - require: `disc_person` is one of `y`
- **Qualified observer and stop control** `c022`
  - gate: `hardware` is one of `y`
  - gate: `hazard_list` is one of `y`
  - require: `observer` is one of `y`
  - require: `stop` is one of `y`
- **Safe state on intervention or disconnection** `c023`
  - gate: `hardware` is one of `y`
  - gate: `hazard_list` is one of `y`
  - require: `safe_i` is one of `y`
  - require: `safe_d` is one of `y`
- **Independent safety limits** `c024`
  - gate: `hardware` is one of `y`
  - gate: `hazard_list` is one of `y`
  - require: `limits` is one of `y`

### Other uses
- **Disclosure at session start or in interface** `c028`
  - gate: `surface` is one of `session`
  - require: (`disc_start` is one of `y` or `disc_ui` is one of `y`)

## Features
- `pur` — observable activities
  - Question: Which listed activities are present?
  - Values: `std` — None of the listed activities; `illegal` — Activity recorded as violating applicable law or regulation; `sabotage` — Infrastructure sabotage; `infra_access` — Critical-system access without authorization; `cyber` — Computer or network compromise; `weapon_dev` — Weapons development; `weapon_op` — Weapons operation; `violence` — Violence; `extremism` — Extremism; `trait_disc` — Protected-trait discrimination; `data` — Sharing personal information; `exploitation` — Exploitation of a person; `grooming` — Grooming of a person; `abuse` — Abuse of a person; `self_harm` — Promotion of self-harm; `harassment` — Harassment; `nc_intimate` — Creating or distributing intimate imagery without consent; `disinfo` — Disinformation; `imp` — Deceptive impersonation; `fake_support` — Fake grassroots support; `conceal_coord` — Concealed coordination; `voter_deception` — Voter deception; `suppression` — Voter suppression; `disruption` — Election disruption; `track` — Tracking a person; `criminal` — Criminal-justice decision; `anon` — Anonymized analysis; `fraud` — Fraud; `scam` — Scam; `spam` — Spam; `false_record` — Falsified record; `guardrail` — Guardrail evasion; `unauth_platform` — Platform access without authorization; `explicit` — Sexually explicit output
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Action, output, approvals, or applicable legal determination; mark an unverified classification unknown.
- `auth` — computer-system authorization
  - Question: Has the responsible system owner authorized the computer or network activity?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Owner authorization and its documented scope
- `cyber_use` — security testing purpose
  - Question: Is this authorized activity security research or bug bounty work?
  - Values: `research` — Security research; `bounty` — Bug bounty work; `other` — Other
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Research plan or bounty program scope
- `cons` — consent to the activity
  - Question: Have all relevant people consented to the specified sharing or tracking?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Consent records tied to that activity
- `age` — subject age
  - Question: How old is the person subject to the action?
  - Values: years (0 to 150)
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Recorded age or date of birth
- `fic` — disclosed fiction, satire or parody
  - Question: Are the relevant outputs disclosed as fiction, satire, or parody?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: The disclosure shown with each relevant output
- `anon_qual` — anonymized analysis qualification recorded
  - Question: Is this anonymized analysis covered by a documented policy exception?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Applicable exception criteria and evidence of their satisfaction
- `area` — recommendation field
  - Question: What field does the recommendation concern?
  - Values: `credit` — Credit; `housing` — Housing; `listed_field` — Another field named explicitly in the policy; `other` — Not a field named in the policy
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Recommendation or an explicit scope list in the policy
- `reviewed` — prior qualified review
  - Question: Did a qualified person review the recommendation before it was used or communicated?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Timestamped review and reviewer qualification
- `changeable` — reviewer can change recommendation
  - Question: Could the reviewing person change the recommendation?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Review tool and reviewer permissions
- `disc_person` — disclosure to affected person
  - Question: Was the affected person told that AI was involved?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Notice issued to the affected person
- `hardware` — hardware control without prior review
  - Question: Does the action control hardware without prior review?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Control command and review record
- `hazard_list` — hazard explicitly listed in scope
  - Question: Does the action present a hazard explicitly named in the relevant policy section?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Applicable policy hazard list and documented physical conditions
- `observer` — qualified observer
  - Question: Is a qualified observer in place?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Designated observer and qualification record
- `stop` — observer can stop equipment
  - Question: Can the designated observer stop the equipment?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Access to a usable stop control
- `safe_i` — intervention response
  - Question: Does the system stop or hold the specified safe state when the observer intervenes?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Test result for operator intervention
- `safe_d` — disconnection response
  - Question: Does the system stop or hold the specified safe state when disconnected?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Test result after connection loss
- `limits` — limits independent of model
  - Question: Are the specified safety limits enforced independently of the model?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Controller and system architecture
- `favorable` — wholly favorable decision
  - Question: Is the decision wholly favorable to the affected person?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Outcome of the proposed decision
- `fav_list` — decision explicitly listed in the exception
  - Question: Is the decision type explicitly listed as eligible for the review exception?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Applicable source list and decision type
- `law_record` — legal permission verified
  - Question: Does an applicable legal determination explicitly confirm this bypass is permitted?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Applicable legal determination for the decision
- `surface` — AI delivery surface
  - Question: Does the AI interaction take place in a session or an interface?
  - Values: `session` — Session or interface; `other` — Neither
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Delivery surface
- `disc_start` — disclosure at session start
  - Question: Is AI disclosed at the start of the session?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: Session-opening transcript or screenshots
- `disc_ui` — disclosure in the interface
  - Question: Is AI disclosed in the interface?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: User-visible interface text

## Rules
| id | title | kind | what to do | source | terms |
| --- | --- | --- | --- | --- | --- |
| `T-c001` | Applicable law and regulations | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c001 |
| `T-c002` | Critical infrastructure | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c002 |
| `T-c003` | Unauthorized computer or network compromise | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c003 |
| `T-c005` | Weapons development or operation | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c005 |
| `T-c006` | Violence, extremism or protected-trait discrimination | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c006 |
| `T-c007` | Sharing personal information without consent | prohibition | Do not share the personal information without consent. | https://example.com/sample-service-terms | c007 |
| `T-c008` | Exploitation, grooming or abuse of a child | prohibition | Do not proceed with the activity involving a person under 18. | https://example.com/sample-service-terms | c008 |
| `T-c010` | Self-harm promotion, harassment or nonconsensual intimate imagery | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c010 |
| `T-c011` | Disinformation or deceptive impersonation | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c011, c012 |
| `T-c013` | Deceptive campaigns | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c013 |
| `T-c014` | Election interference | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c014 |
| `T-c015` | Nonconsensual tracking or criminal-justice decisions | prohibition | Do not proceed with the applicable tracking or criminal-justice activity. | https://example.com/sample-service-terms | c015 |
| `T-c017` | Fraud, scams, spam or falsified records | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c017 |
| `T-c018` | Platform abuse | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c018 |
| `T-c019` | Sexually explicit output | prohibition | Do not proceed with the activity covered by this term. | https://example.com/sample-service-terms | c019 |
| `T-c020` | Qualified prior review | obligation | Have a qualified person review the recommendation beforehand and give them the ability to change it. | https://example.com/sample-service-terms | c020, c027 |
| `T-c021` | Disclosure to an affected person | obligation | Tell the affected person that AI was involved. | https://example.com/sample-service-terms | c021 |
| `T-c022` | Qualified observer and stop control | obligation | Put a qualified observer in place and give them a usable stop control. | https://example.com/sample-service-terms | c022 |
| `T-c023` | Safe state on intervention or disconnection | obligation | Make the equipment stop or stay in a safe state on intervention and on disconnection. | https://example.com/sample-service-terms | c023 |
| `T-c024` | Independent safety limits | obligation | Enforce the safety limits independently of the model. | https://example.com/sample-service-terms | c024 |
| `T-c028` | Disclosure at session start or in interface | obligation | Disclose AI at session start or in the interface. | https://example.com/sample-service-terms | c028 |

## Terms

**c001** · General rules › Illegal activity · prohibition

> Do not use the service to break a law or regulation that applies to you.

**c002** · General rules › Critical infrastructure · prohibition

> Summary (not a quote): No sabotage of infrastructure and no unapproved access to critical systems.

**c003** · General rules › Computer and network systems · prohibition

> Summary (not a quote): No breaking into computers or networks without permission.

**c004** · General rules › Computer and network systems · permission_exception

> Summary (not a quote): Authorized security research, including bug bounties, is permitted.

links: modifies → c003

**c005** · General rules › Weapons · prohibition

> Summary (not a quote): No building, testing or operating weapons.

**c006** · General rules › Violence and hate · prohibition

> Summary (not a quote): No violent, extremist or discriminatory content.

**c007** · General rules › Privacy · prohibition

> Do not disclose another person's personal data unless that person has agreed.

**c008** · General rules › Minors · prohibition

> Summary (not a quote): No content that exploits, grooms or harms a child.

links: uses_definition → c009

**c009** · General rules › Minors · definition

> A child is any person younger than 18.

**c010** · General rules › Harmful conduct · prohibition

> Summary (not a quote): No encouraging self-harm, no harassment and no intimate images shared without consent.

**c011** · General rules › False information · prohibition

> Summary (not a quote): No false information and no impersonation meant to deceive.

**c012** · General rules › False information · permission_exception

> Summary (not a quote): Clearly labelled fiction, satire, and parody are allowed.

links: modifies → c011

**c013** · General rules › Deceptive campaigns · prohibition

> Summary (not a quote): No fake grassroots campaigns or hidden coordination.

**c014** · General rules › Elections · prohibition

> Summary (not a quote): No misleading voters, keeping people from voting or disrupting elections.

**c015** · General rules › Tracking and enforcement · prohibition

> Summary (not a quote): No tracking people without consent and no criminal-justice decisions.

**c016** · General rules › Tracking and enforcement · permission_exception

> Summary (not a quote): Consented tracking and anonymised analysis may be allowed.

links: modifies → c015

**c017** · General rules › Fraud · prohibition

> Summary (not a quote): No fraud, scams, spam or forged records.

**c018** · General rules › Service abuse · prohibition

> Summary (not a quote): No getting around safeguards and no unapproved access to the service.

**c019** · General rules › Explicit content · prohibition

> Summary (not a quote): No sexually explicit output.

**c020** · Sensitive uses › Requirements · obligation

> Summary (not a quote): Before delivery, a qualified person reviews the recommendations and can change them.

links: uses_definition → c025

**c021** · Sensitive uses › Requirements · obligation

> Summary (not a quote): Tell the affected person that AI was involved.

links: uses_definition → c025

**c022** · Sensitive uses › Requirements · obligation

> Summary (not a quote): A qualified person can watch the equipment and stop it.

links: uses_definition → c026

**c023** · Sensitive uses › Requirements · obligation

> Summary (not a quote): Stop or stay safe when someone intervenes or the link drops.

links: uses_definition → c026

**c024** · Sensitive uses › Requirements · obligation

> Summary (not a quote): Keep safety limits enforced outside the model.

links: uses_definition → c026

**c025** · Sensitive uses › Sensitive recommendations · definition

> Summary (not a quote): Covered recommendations are listed fields such as credit and housing.

**c026** · Sensitive uses › Physical actions · definition

> Summary (not a quote): Covered actions are hardware control without review where listed hazards exist.

**c027** · Sensitive uses › Favourable decisions · permission_exception

> Summary (not a quote): Where the law allows, wholly favourable listed decisions may bypass prior review.

links: modifies → c020

**c028** · Other uses · obligation

> Summary (not a quote): Disclose AI at the start of a session or in the interface.

## Examples
| code | verdict | violated |
| --- | --- | --- |
| `pur=illegal` | violates | T-c001 |
| `pur=std` | needs_info |  |
| `pur=sabotage` | violates | T-c002 |
| `pur=infra_access` | violates | T-c002 |
| `pur=cyber auth=n` | violates | T-c003 |
| `pur=std auth=n` | needs_info |  |
| `pur=cyber auth=y` | needs_info |  |
| `pur=weapon_dev` | violates | T-c005 |
| `pur=weapon_op` | violates | T-c005 |
| `pur=violence` | violates | T-c006 |
| `pur=extremism` | violates | T-c006 |
| `pur=trait_disc` | violates | T-c006 |
| `pur=data cons=n` | violates | T-c007 |
| `pur=std cons=n` | needs_info |  |
| `pur=data cons=y` | needs_info |  |
| `pur=exploitation age=0` | violates | T-c008 |
| `pur=std age=0` | needs_info |  |
| `pur=grooming age=0` | violates | T-c008 |
| `pur=abuse age=0` | violates | T-c008 |
| `pur=exploitation age=18` | needs_info |  |
| `pur=exploitation age=17` | violates | T-c008 |
| `pur=exploitation age=19` | needs_info |  |
| `pur=self_harm` | violates | T-c010 |
| `pur=harassment` | violates | T-c010 |
| `pur=nc_intimate` | violates | T-c010 |
| `pur=disinfo fic=n` | violates | T-c011 |
| `pur=disinfo` | needs_info |  |
| `pur=imp` | needs_info |  |
| `pur=disinfo fic=y` | needs_info |  |
| `pur=fake_support` | violates | T-c013 |
| `pur=conceal_coord` | violates | T-c013 |
| `pur=voter_deception` | violates | T-c014 |
| `pur=suppression` | violates | T-c014 |
| `pur=disruption` | violates | T-c014 |
| `pur=track cons=n` | violates | T-c015 |
| `pur=criminal` | violates | T-c015 |
| `pur=track cons=y` | needs_info |  |
| `pur=criminal cons=y` | violates | T-c015 |
| `pur=fraud` | violates | T-c017 |
| `pur=scam` | violates | T-c017 |

## Saved codes
None.

## Not encoded
- `c004` — Authorized research and bounty work are already outside c003’s unauthorized-activity gate. The summary supplies no objectively identifiable exception inside that gate.
- `c016` — Consented tracking is already outside c015’s tracking gate, and the summary does not state which anonymized analyses qualify, what prohibition they excuse, or the conditions of qualification.

## Self-exam
| check | score | threshold | passed |
| --- | --- | --- | --- |
| validate | — | — | yes |
| terms_coverage | 1.0 | 1.0 | yes |
| key_anchors | 1.0 | 1.0 | yes |
| key_agreement | — | 0.8 | skipped |
| map_reach | 1.0 | 1.0 | yes |
| references | 1.0 | 1.0 | yes |
| rule_coverage | 1.0 | 1.0 | yes |
| mutation_score | 1.0 | 0.8 | yes |
| properties | — | — | yes |

## History evaluation (not a gate)
Not run for this exact bundle. Encoded history can be evaluated after the build.

_A structured self-check, not legal advice._
