from dataclasses import dataclass, field


@dataclass
class PlayerStats:
    score: int = 0
    guesses: int = 0
    correct: int = 0


@dataclass
class GameState:
    scores: dict = field(default_factory=dict)

    def ensure(self, user: str) -> PlayerStats:
        if user not in self.scores:
            self.scores[user] = PlayerStats()
        return self.scores[user]

    def award(self, user: str, points: int = 1):
        s = self.ensure(user)
        s.score += points
        s.correct += 1

    def record_guess(self, user: str):
        self.ensure(user).guesses += 1

    def leaderboard(self, n: int = 5) -> list[tuple[str, int]]:
        return sorted(
            ((u, s.score) for u, s in self.scores.items()),
            key=lambda x: x[1],
            reverse=True,
        )[:n]
