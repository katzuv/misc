import dataclasses


@dataclasses.dataclass
class Team:
    number: str
    name: str
    location: str
    year_spans: tuple[tuple[int, int], ...]

    def __str__(self):
        year_spans = self._prettify_year_spans()
        return (
            f"#{self.number} - {self.name}, {self.location}. Active years: {year_spans}"
        )

    def _prettify_year_spans(self) -> str:
        """
        :return: prettified year spans the team is active
        """
        output_parts = []
        for span in self.year_spans:
            if len(span) == 1:
                year = span[0]
                output_parts.append(str(year))
            else:
                first_year, last_year = span
                output_parts.append(f"{first_year}-{last_year}")

        return ", ".join(output_parts)
