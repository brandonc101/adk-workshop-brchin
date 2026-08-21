# adk-workshop-brchin

Challenge lab work for the Agent Development Kit (ADK) workshop.

| Lab | Description |
| --- | --- |
| [ChallengeLab1](./ChallengeLab1) | Weather agent — real-time US weather via the NWS API and Google Maps geocoding, with Gemini + third-party model support. |
| [ChallengeLab2](./ChallengeLab2) | Weather agent + ADK callbacks — logs user prompts and model responses, and validates input (US-only + Google Cloud Model Armor malicious-content screening). |
| [ChallengeLab3](./ChallengeLab3) | Multi-agent system — a coordinator (root) agent delegates to a weather sub-agent and a Google Search sub-agent; test harness prints the event stream. |
| [ChallengeLab4](./ChallengeLab4) | Answer-team workflow — a coordinator routes to a greeter, a weather agent, or a Sequential answer team (search → critique → refine) that answers, verifies, and refines responses. |
| [ChallengeLab5](./ChallengeLab5) | Deployment — deploys the Lab 4 agent to Vertex AI Agent Engine (Agent Platform) with `deploy.py`, and verifies it live with `test_deployment.py`. |

Each lab is self-contained in its own directory. See that directory's
`README.md` for setup and run instructions.
