# LifeOS

A personal AI operating layer for [Claude Code](https://claude.ai/claude-code), built for WSL2/Linux and tailored to one specific use case: intraday equities trading automation.

## What This Is

LifeOS turns Claude Code into a persistent, skill-based AI system with:

- **The Algorithm** — a structured, multi-phase execution framework (Observe → Think → Plan → Build → Execute → Verify → Learn) that produces verifiable outcomes using Ideal State Criteria
- **Skills** — modular capability packages with workflows, tools, and routing (trading game plans, daily reviews, research, systems thinking, economic metrics)
- **Hooks** — lifecycle event handlers for security validation, context management, session learning, and system integrity
- **Memory** — persistent file-based memory for user context, project state, and learning reflections
- **TELOS** — a life operating system for tracking goals, projects, challenges, and personal growth

## Origin and Divergence

This project started from the ideas in Daniel Miessler's [Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure) and [TheAlgorithm](https://github.com/danielmiessler/TheAlgorithm). It is **not a fork** and does not track upstream — the two projects have diverged enough that treating this as a fork would be misleading rather than useful.

The concrete differences that drove the split:

- **Platform:** this build runs on WSL2/FedoraLinux under Windows. The original is developed on macOS. Tooling, paths, and system integrations that make sense on a Mac often don't apply here, and vice versa.
- **Use case:** this build is purpose-built around a live intraday trading operation — broker integration (DAS Trader Pro), real-time market-data tooling, risk/discipline rules, and a daily gameplan/report-card workflow. That shaped most of the architecture decisions that have since diverged from the original.
- **Maintenance:** this repo moves independently, on its own schedule, driven by what the trading workflow actually needs rather than by upstream changes.

## Structure

```
~/.claude/
├── PAI/                    # Core system (Algorithm, context routing, tools)
│   └── Algorithm/          # Versioned execution framework
├── skills/                 # Modular capabilities
│   ├── Trading/            # Market analysis, game plans, trade review
│   ├── Research/           # Multi-agent parallel research
│   ├── Thinking/           # FirstPrinciples, Council, RedTeam, Science
│   ├── Telos/              # Life OS — goals, projects, learning
│   ├── Agents/              # Custom agent composition
│   ├── USMetrics/          # Economic indicators
│   └── Utilities/          # System tools (upgrade, scaffolding, delegation)
├── hooks/                  # Lifecycle event handlers
├── MEMORY/                 # Persistent state (work, reflections, snapshots)
└── settings.json           # Configuration (permissions, hooks, MCP)
```

## Getting Started

1. Install [Claude Code](https://claude.ai/claude-code)
2. Copy this framework to `~/.claude/`
3. Create your `PAI/USER/` directory with your own TELOS, projects, and customizations
4. Create a `settings.json` from `settings.json.template`

This has only been run on WSL2/FedoraLinux. Other Linux distributions will likely work with minor adjustments; macOS is untested and may need more.

## License

MIT — use it, fork it, make it yours.

## Acknowledgments

- **[Daniel Miessler](https://danielmiessler.com)** — original architect of [Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure) and [TheAlgorithm](https://github.com/danielmiessler/TheAlgorithm), and creator of [TELOS](https://danielmiessler.com/telos). This project started from his ideas, even though it no longer tracks his code.
- **Anthropic** — for Claude Code and the model that makes this possible.
