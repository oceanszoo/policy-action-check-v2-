---
name: pac-sample-bundle
description: Check an action against Sample Service Terms (synthetic test fixture) with no model, using the policy-action-check bundle in this folder.
---
# Sample Service Terms (synthetic test fixture): policy action bundle

https://example.com/sample-service-terms · format 1.6 · self-exam: passed (2026-11-20T06:32:53+00:00) · 105 categories, 15 features, 21 rules <!-- bundle data: 279e29985fe4ea52604391f18edc335005f84ed087a4f30402070f01149cd368 -->

## How to use
- Web app: open pac-reader.html and load this folder.
- Command line: `python3 pac.py --space <this folder> report "pur=cyber auth=own"`, plus `categories`, `fit "<code>"`, `check`, `lookup "<words>"`.
- Codes: `key=value` tokens; `a+b` for several values on a multi-valued key; `&` = at the same time, `>` = after.

## Case map
- **Chatbot or assistant** `chat` — A model talks with people, for example a support bot or a companion app. Preset: `chat=y`.
  - **Everyday help** `chat/everyday` — No high-risk advice and no listed function. Preset: `pur=std chat=y`.
  - **Advice in a high-risk area** `chat/advice` — Legal, medical, financial and similar advice. Preset: `pur=std chat=y`.
    - **Legal** `chat/advice/legal` — No description. Preset: `pur=std hr=legal chat=y`.
    - **Medical or mental health** `chat/advice/med` — No description. Preset: `pur=std hr=med chat=y`.
    - **Finance** `chat/advice/fin` — No description. Preset: `pur=std hr=fin chat=y`.
    - **Credit** `chat/advice/credit` — No description. Preset: `pur=std hr=credit chat=y`.
    - **Insurance** `chat/advice/ins` — No description. Preset: `pur=std hr=ins chat=y`.
    - **Housing** `chat/advice/housing` — No description. Preset: `pur=std hr=housing chat=y`.
    - **Employment** `chat/advice/emp` — No description. Preset: `pur=std hr=emp chat=y`.
    - **Education or credentials** `chat/advice/edu` — No description. Preset: `pur=std hr=edu chat=y`.
    - **Healthcare access** `chat/advice/health` — No description. Preset: `pur=std hr=health chat=y`.
    - **Public benefits** `chat/advice/benefit` — No description. Preset: `pur=std hr=benefit chat=y`.
    - **Legal status** `chat/advice/status` — No description. Preset: `pur=std hr=status chat=y`.
- **Recommendation in a high-risk area** `advice` — Legal, medical, financial, insurance, housing, work and similar areas. Preset: `(none)`.
  - **Legal** `advice/legal` — No description. Preset: `hr=legal`.
    - **About a specific person** `advice/legal/person` — about a specific individual, delivered or used for a decision. Preset: `hr=legal scope=ind`.
      - **Wholly favorable decision** `advice/legal/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=legal scope=ind fav=full`.
      - **Other or adverse decision** `advice/legal/person/other` — anything else, incl. partial or conditional. Preset: `hr=legal scope=ind fav=part`.
    - **Not covered** `advice/legal/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=legal scope=nc`.
  - **Medical or mental health** `advice/med` — No description. Preset: `hr=med`.
    - **About a specific person** `advice/med/person` — about a specific individual, delivered or used for a decision. Preset: `hr=med scope=ind`.
      - **Wholly favorable decision** `advice/med/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=med scope=ind fav=full`.
      - **Other or adverse decision** `advice/med/person/other` — anything else, incl. partial or conditional. Preset: `hr=med scope=ind fav=part`.
    - **Not covered** `advice/med/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=med scope=nc`.
  - **Finance** `advice/fin` — No description. Preset: `hr=fin`.
    - **About a specific person** `advice/fin/person` — about a specific individual, delivered or used for a decision. Preset: `hr=fin scope=ind`.
      - **Wholly favorable decision** `advice/fin/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=fin scope=ind fav=full`.
      - **Other or adverse decision** `advice/fin/person/other` — anything else, incl. partial or conditional. Preset: `hr=fin scope=ind fav=part`.
    - **Not covered** `advice/fin/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=fin scope=nc`.
  - **Credit** `advice/credit` — No description. Preset: `hr=credit`.
    - **About a specific person** `advice/credit/person` — about a specific individual, delivered or used for a decision. Preset: `hr=credit scope=ind`.
      - **Wholly favorable decision** `advice/credit/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=credit scope=ind fav=full`.
      - **Other or adverse decision** `advice/credit/person/other` — anything else, incl. partial or conditional. Preset: `hr=credit scope=ind fav=part`.
    - **Not covered** `advice/credit/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=credit scope=nc`.
  - **Insurance** `advice/ins` — No description. Preset: `hr=ins`.
    - **About a specific person** `advice/ins/person` — about a specific individual, delivered or used for a decision. Preset: `hr=ins scope=ind`.
      - **Wholly favorable decision** `advice/ins/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=ins scope=ind fav=full`.
      - **Other or adverse decision** `advice/ins/person/other` — anything else, incl. partial or conditional. Preset: `hr=ins scope=ind fav=part`.
    - **Not covered** `advice/ins/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=ins scope=nc`.
  - **Housing** `advice/housing` — No description. Preset: `hr=housing`.
    - **About a specific person** `advice/housing/person` — about a specific individual, delivered or used for a decision. Preset: `hr=housing scope=ind`.
      - **Wholly favorable decision** `advice/housing/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=housing scope=ind fav=full`.
      - **Other or adverse decision** `advice/housing/person/other` — anything else, incl. partial or conditional. Preset: `hr=housing scope=ind fav=part`.
    - **Not covered** `advice/housing/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=housing scope=nc`.
  - **Employment** `advice/emp` — No description. Preset: `hr=emp`.
    - **About a specific person** `advice/emp/person` — about a specific individual, delivered or used for a decision. Preset: `hr=emp scope=ind`.
      - **Wholly favorable decision** `advice/emp/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=emp scope=ind fav=full`.
      - **Other or adverse decision** `advice/emp/person/other` — anything else, incl. partial or conditional. Preset: `hr=emp scope=ind fav=part`.
    - **Not covered** `advice/emp/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=emp scope=nc`.
  - **Education or credentials** `advice/edu` — No description. Preset: `hr=edu`.
    - **About a specific person** `advice/edu/person` — about a specific individual, delivered or used for a decision. Preset: `hr=edu scope=ind`.
      - **Wholly favorable decision** `advice/edu/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=edu scope=ind fav=full`.
      - **Other or adverse decision** `advice/edu/person/other` — anything else, incl. partial or conditional. Preset: `hr=edu scope=ind fav=part`.
    - **Not covered** `advice/edu/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=edu scope=nc`.
  - **Healthcare access** `advice/health` — No description. Preset: `hr=health`.
    - **About a specific person** `advice/health/person` — about a specific individual, delivered or used for a decision. Preset: `hr=health scope=ind`.
      - **Wholly favorable decision** `advice/health/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=health scope=ind fav=full`.
      - **Other or adverse decision** `advice/health/person/other` — anything else, incl. partial or conditional. Preset: `hr=health scope=ind fav=part`.
    - **Not covered** `advice/health/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=health scope=nc`.
  - **Public benefits** `advice/benefit` — No description. Preset: `hr=benefit`.
    - **About a specific person** `advice/benefit/person` — about a specific individual, delivered or used for a decision. Preset: `hr=benefit scope=ind`.
      - **Wholly favorable decision** `advice/benefit/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=benefit scope=ind fav=full`.
      - **Other or adverse decision** `advice/benefit/person/other` — anything else, incl. partial or conditional. Preset: `hr=benefit scope=ind fav=part`.
    - **Not covered** `advice/benefit/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=benefit scope=nc`.
  - **Legal status** `advice/status` — No description. Preset: `hr=status`.
    - **About a specific person** `advice/status/person` — about a specific individual, delivered or used for a decision. Preset: `hr=status scope=ind`.
      - **Wholly favorable decision** `advice/status/person/favorable` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit). Preset: `hr=status scope=ind fav=full`.
      - **Other or adverse decision** `advice/status/person/other` — anything else, incl. partial or conditional. Preset: `hr=status scope=ind fav=part`.
    - **Not covered** `advice/status/not-covered` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules. Preset: `hr=status scope=nc`.
- **Security or systems work** `security` — Testing, scanning or changing computer systems and networks. Preset: `pur=cyber`.
  - **Own or authorized systems** `security/own` — No description. Preset: `pur=cyber auth=own`.
  - **Systems without permission** `security/unauth` — No description. Preset: `pur=cyber auth=unauth`.
  - **No target system** `security/none` — For example writing about security in general. Preset: `pur=cyber auth=na`.
- **Content creation** `content` — Writing, images or media, including fiction and persuasion. Preset: `(none)`.
  - **Impersonate a real person or organization** `content/imp` — No description. Preset: `pur=imp`.
    - **Clearly labelled parody, satire or fiction** `content/imp/labelled` — No description. Preset: `pur=imp fic=lab`.
    - **Presented as real** `content/imp/real` — No description. Preset: `pur=imp fic=real`.
  - **Spread false information** `content/false` — No description. Preset: `pur=false`.
  - **Fake personas, accounts, outlets or inauthentic campaign** `content/fake` — No description. Preset: `pur=fake`.
  - **Interfere with elections or voting** `content/elect` — No description. Preset: `pur=elect`.
  - **Violence, extremism or hate** `content/viol` — No description. Preset: `pur=viol`.
  - **Sexually explicit content** `content/sex` — No description. Preset: `pur=sex`.
  - **Ordinary content** `content/std` — No description. Preset: `pur=std`.
- **Personal data or tracking** `data` — Collecting, matching or watching information about people. Preset: `(none)`.
  - **Collect, aggregate or process private data** `data/data` — No description. Preset: `pur=data`.
    - **People agreed** `data/data/consent` — No description. Preset: `pur=data cons=y`.
    - **People did not agree** `data/data/no-consent` — No description. Preset: `pur=data cons=n`.
  - **Track or profile people** `data/track` — No description. Preset: `pur=track`.
    - **People agreed** `data/track/consent` — No description. Preset: `pur=track cons=y`.
    - **People did not agree** `data/track/no-consent` — No description. Preset: `pur=track cons=n`.
- **Robot or physical device** `physical` — A model controls something that moves or acts in the world. Preset: `(none)`.
  - **High-risk physical action** `physical/high-risk` — No description. Preset: `phys=hi`.
  - **Not covered** `physical/not-covered` — not covered: consumer device in built-in limits, reviewed plan, monitoring only, non-hazardous enclosed lab. Preset: `phys=nc`.
- **Other listed functions** `listed` — Weapons, infrastructure, minors, fraud, platform abuse and similar. Preset: `(none)`.
  - **Disrupt critical infrastructure** `listed/infra` — No description. Preset: `pur=infra`.
  - **Weapons, including CBRN** `listed/weap` — No description. Preset: `pur=weap`.
  - **Harm to minors** `listed/child` — No description. Preset: `pur=child`.
  - **Self-harm promotion, harassment, non-consensual intimate imagery** `listed/harm` — No description. Preset: `pur=harm`.
  - **Make law-enforcement or criminal-justice decisions** `listed/lawenf` — No description. Preset: `pur=lawenf`.
  - **Emotion recognition (not medical or safety)** `listed/emo` — No description. Preset: `pur=emo`.
  - **Scams, phishing, extortion, spam, fake documents, plagiarism** `listed/fraud` — No description. Preset: `pur=fraud`.
  - **Platform abuse: reselling, multi-account, distillation, ban evasion, jailbreak** `listed/abuse` — No description. Preset: `pur=abuse`.
  - **Other illegal activity** `listed/illegal` — No description. Preset: `pur=illegal`.
- **Something else** `other` (catch-all) — Start from every feature. Preset: `(none)`.

## Features
- `act` — actor
  - Question: Who performs the action: a consumer, a business or API developer, or a deployed agent?
  - Values: `con` — consumer user; `biz` — business or API developer; `agt` — deployed agent
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: account type / contract (consumer terms vs commercial API agreement); agent deployment config
- `pur` — what the action does (observable functions; one or more, written a+b)
  - Question: What does the action do? Pick every function that applies.
  - Values: `std` — ordinary function, none of the listed ones (incl. emotion detection for medical or safety use); `data` — collect, aggregate or process private data; `track` — track or profile people; `imp` — impersonate a real person or organization; `false` — spread false information; `fake` — fake personas, accounts, outlets or inauthentic campaign; `elect` — interfere with elections or voting; `cyber` — intrusion, exploitation or malware; `infra` — disrupt critical infrastructure; `weap` — weapons, including CBRN; `viol` — violence, extremism or hate; `child` — harm to minors; `harm` — self-harm promotion, harassment, non-consensual intimate imagery; `lawenf` — make law-enforcement or criminal-justice decisions; `emo` — emotion recognition (not medical or safety); `fraud` — scams, phishing, extortion, spam, fake documents, plagiarism; `abuse` — platform abuse: reselling, multi-account, distillation, ban evasion, jailbreak; `sex` — sexually explicit content; `illegal` — other illegal activity
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: no
  - Evidence: what the action does or produces, judged from the request, output or tool call, not from stated intentions
- `auth` — authorization of the target
  - Question: Is the target system yours or are you authorized to test it?
  - Values: `na` — no target system; `own` — own or authorized target; `unauth` — unauthorized target
  - Default: none (unknown if unset)
  - Inside: `pur` is one of `cyber`
  - Can be fixed: yes
  - Evidence: written authorization or ownership record for the target system (scope letter, bug bounty terms)
- `cons` — consent of affected people (privacy)
  - Question: Did the affected people agree to this?
  - Values: `na` — no affected people; `y` — they agreed; `n` — they did not agree
  - Default: none (unknown if unset)
  - Inside: `pur` is one of `data`, `track`
  - Can be fixed: yes
  - Evidence: consent or opt-in record of the affected people (terms acceptance, signed form)
- `fic` — framing
  - Question: Is the content clearly labelled as parody, satire or fiction, or presented as real?
  - Values: `na` — not relevant; `lab` — clearly labelled parody, satire or fiction; `real` — presented as real
  - Default: none (unknown if unset)
  - Inside: `pur` is one of `imp`
  - Can be fixed: yes
  - Evidence: label visible in the published work itself
- `hr` — high-risk recommendation area
  - Question: Does the output recommend something in one of these high-risk areas?
  - Values: `none` — none; `legal` — legal; `med` — medical or mental health; `fin` — finance; `credit` — credit; `ins` — insurance; `housing` — housing; `emp` — employment; `edu` — education or credentials; `health` — healthcare access; `benefit` — public benefits; `status` — legal status
  - Default: `none`
  - Inside: all cases
  - Can be fixed: no
  - Evidence: the subject matter of the output (legal, medical, credit, ...) as written
- `scope` — recommendation scope
  - Question: Is the recommendation about a specific person and delivered to them or used to decide about them?
  - Values: `na` — no recommendation; `ind` — about a specific individual, delivered or used for a decision; `nc` — not covered: education, wellness, internal drafting, explaining given advice, fixed rules
  - Default: `na`
  - Inside: `hr` is none of `none`
  - Can be fixed: no
  - Evidence: whether the output names a specific person and is delivered to them or used for their decision
- `fav` — decision direction
  - Question: Which direction is the decision?
  - Values: `na` — no decision; `full` — wholly favorable listed decision (pay claim, approve care, grant eligibility or benefit); `part` — anything else, incl. partial or conditional
  - Default: `na`
  - Inside: `scope` is one of `ind`
  - Can be fixed: no
  - Evidence: the decision's content: full approval of a listed decision vs anything else
- `rev` — qualified human review before delivery or use
  - Question: Does a qualified person review it, and can they change it, before it is delivered or used?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: `scope` is one of `ind`
  - Can be fixed: yes
  - Evidence: review log: who reviewed, their qualification, and that they could change the output before delivery
- `disc` — AI disclosure to the affected person or chat user
  - Question: Are the affected people or chat users told they are dealing with AI?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: all cases
  - Can be fixed: yes
  - Evidence: the notice text shown to the person (template, UI screenshot)
- `chat` — consumer-facing chatbot or agent
  - Question: Is this a chatbot or agent that consumers talk to directly?
  - Values: `y` — yes; `n` — no
  - Default: `n`
  - Inside: all cases
  - Can be fixed: no
  - Evidence: whether the product talks directly with consumers
- `phys` — physical action
  - Question: Does the action move or control anything physical?
  - Values: `none` — none; `hi` — high-risk physical action; `nc` — not covered: consumer device in built-in limits, reviewed plan, monitoring only, non-hazardous enclosed lab
  - Default: `none`
  - Inside: all cases
  - Can be fixed: no
  - Evidence: whether model output drives equipment, and which category
- `stop` — human can observe and stop
  - Question: Can a person watch it and stop it at any time?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: `phys` is one of `hi`
  - Can be fixed: yes
  - Evidence: operator stop control exists and is tested
- `safe` — safe state on intervention or connection loss
  - Question: Does it go to a safe state when someone intervenes or the connection drops?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: `phys` is one of `hi`
  - Can be fixed: yes
  - Evidence: tested behaviour on operator intervention and connection loss
- `lim` — operating limits enforced outside the model
  - Question: Are its operating limits enforced outside the model (hardware or software interlocks)?
  - Values: `y` — yes; `n` — no
  - Default: none (unknown if unset)
  - Inside: `phys` is one of `hi`
  - Can be fixed: yes
  - Evidence: speed/force/dose limits configured in a controller independent of the model

## Rules
| id | title | kind | what to do | source | terms |
| --- | --- | --- | --- | --- | --- |
| `P-illegal` | Illegal activity | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: illegal activity | c001 |
| `P-critical-infra` | Critical infrastructure | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: critical infrastructure | c002 |
| `P-cyber` | Computer and network systems | prohibition | Work only on systems you own or have written authorization to test; otherwise do not proceed. | General rules: computer and network systems | c003, c004 |
| `P-weapons` | Weapons | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: weapons | c005 |
| `P-violence-hate` | Violence and hate | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: violence and hate | c006 |
| `P-privacy` | Privacy and identity | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: privacy and identity | c007 |
| `P-child-safety` | Children's safety | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: children's safety | c008 |
| `P-harmful-conduct` | Cruel or harmful conduct | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: cruel or harmful conduct | c010 |
| `P-disinformation` | Disinformation | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: disinformation | c011, c012 |
| `P-deceptive-campaigns` | Deceptive campaigns | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: deceptive campaigns | c013 |
| `P-elections` | Democratic processes | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: democratic processes | c014 |
| `P-surveillance` | Surveillance, censorship and law enforcement | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: surveillance, censorship and law enforcement | c015, c016 |
| `P-fraud` | Fraud and predatory practices | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: fraud and predatory practices | c017 |
| `P-platform-abuse` | Platform abuse | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: platform abuse | c018 |
| `P-sexual-content` | Sexually explicit content | prohibition | Do not proceed with this action: it is prohibited regardless of safeguards. | General rules: sexually explicit content | c019 |
| `O-hr-review` | Qualified human-in-the-loop | obligation | Have a qualified person (licensed where required) review the recommendation, with power to change it, before it is delivered or used. | Sensitive uses: qualified human-in-the-loop | c020, c027 |
| `O-hr-disclosure` | Disclosure | obligation | Tell the person receiving the advice or decision, clearly, that AI was used. | Sensitive uses: disclosure | c021 |
| `O-physical-stop` | Observe and stop | obligation | Give a qualified operator a way to observe the equipment and stop it at any time. | Physical equipment: observe and stop | c022 |
| `O-physical-safe-state` | Safe state | obligation | Make the equipment stop or hold a safe state when the operator intervenes or the connection drops. | Physical equipment: safe state | c023 |
| `O-physical-limits` | Independent limits | obligation | Enforce operating limits (speed, force, dose, temperature) in a controller independent of the model. | Physical equipment: independent limits | c024 |
| `O-chatbot-disclosure` | Consumer chatbots disclose AI | obligation | Show users that they are talking to an AI, at least at the start of each session or in the interface. | Other uses: consumer chatbots disclose AI | c028 |

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
| `pur=cyber auth=own` | compliant |  |
| `pur=cyber auth=unauth` | violates | P-cyber |
| `pur=track cons=y` | compliant |  |
| `pur=track cons=n` | violates | P-surveillance |
| `pur=imp fic=lab` | compliant |  |
| `pur=imp fic=real` | violates | P-disinformation |
| `@claim-pay rev=n` | compliant |  |
| `act=biz pur=std hr=ins scope=ind fav=part rev=n` | violates | O-hr-review |
| `act=biz pur=std hr=emp scope=ind fav=part rev=y disc=y` | compliant |  |
| `act=biz pur=std hr=med scope=nc` | compliant |  |
| `@support-bot` | compliant_if_requirements_met |  |
| `@support-bot disc=n` | violates | O-chatbot-disclosure |
| `@robot-shared stop=y safe=y lim=y` | compliant |  |
| `@robot-shared stop=y safe=y lim=n` | violates | O-physical-limits |
| `act=biz pur=std phys=nc` | compliant |  |
| `pur=abuse` | violates | P-platform-abuse |
| `pur=data` | needs_info |  |
| `pur=std hr=ins scope=ind fav=part rev=y disc=y date=2026-11-01` | compliant |  |
| `act=biz pur=data+cyber auth=own cons=y` | compliant |  |
| `act=biz pur=track+fraud cons=y` | violates | P-fraud |
| `act=biz pur=cyber+data auth=own` | needs_info |  |
| `act=biz pur=illegal` | violates | P-illegal |
| `act=biz pur=infra` | violates | P-critical-infra |
| `act=biz pur=weap` | violates | P-weapons |
| `act=biz pur=viol` | violates | P-violence-hate |
| `act=biz pur=data cons=n` | violates | P-privacy |
| `act=biz pur=child` | violates | P-child-safety |
| `act=biz pur=harm` | violates | P-harmful-conduct |
| `act=biz pur=fake` | violates | P-deceptive-campaigns |
| `act=biz pur=elect` | violates | P-elections |
| `act=biz pur=sex` | violates | P-sexual-content |
| `act=biz phys=hi` | compliant_if_requirements_met |  |
| `act=biz pur=std chat=y disc=y` | compliant |  |
| `act=biz pur=std fic=real` | compliant |  |
| `act=biz pur=std cons=n` | compliant |  |
| `act=biz pur=std hr=none scope=ind fav=part` | compliant |  |
| `act=biz pur=false` | violates | P-disinformation |
| `act=biz pur=emo` | violates | P-surveillance |

## Saved codes
- `@claim-pay` — `act=biz pur=std hr=ins scope=ind fav=full disc=y`
- `@hr-advice` — `act=biz pur=std hr=legal scope=ind fav=part`
- `@robot-shared` — `act=biz pur=std phys=hi`
- `@support-bot` — `act=biz pur=std chat=y`

## Self-exam
| check | score | threshold | passed |
| --- | --- | --- | --- |
| validate | — | — | yes |
| terms_coverage | — | 1.0 | skipped |
| references | 1.0 | 1.0 | yes |
| rule_coverage | 1.0 | 1.0 | yes |
| replay_agreement | — | 0.9 | skipped |
| replay_decisive | — | 0.8 | skipped |
| mutation_score | 1.0 | 0.8 | yes |
| properties | — | — | yes |
| map_fit | 1.0 | 0.8 | yes |

_A structured self-check, not legal advice._
