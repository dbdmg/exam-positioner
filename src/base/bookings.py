import polars as pl


class Bookings:
    def __init__(self, files: list[str]):
        bookings = pl.concat([pl.read_csv(file) for file in files])

        # Select DSA bookings
        self.dsa = bookings.filter(
            pl.col("NOTE").str.contains("Dsa")
            | pl.col("NOTE").str.contains("Tempo aggiuntivo")
        )
        bookings = bookings.filter(pl.col("MATRICOLA").is_in(self.dsa).not_())

        # Select NoPC bookings
        self.no_pc = bookings.filter(pl.col("NOTE").str.contains("NoPC"))
        bookings = bookings.filter(pl.col("MATRICOLA").is_in(self.no_pc).not_())

        # Select onsite bookings
        self.on_site = bookings.filter(
            pl.col("NOTE").str.contains("Esame online").not_()
            | pl.col("NOTE").is_null()
        )

        self.assignations = []

    def assign_to_room(self, id: int, room: str):
        self.assignations.append({"MATRICOLA": id, "AULA": room})

    def unassigned(self):
        assignations = pl.DataFrame(self.assignations)
        assigned_ids = set(assignations["MATRICOLA"]) if self.assignations else set()
        unassigned = self.on_site.filter(pl.col("MATRICOLA").is_in(assigned_ids).not_())

        return unassigned

    def save_assignations(self, path: str):
        assignation = pl.DataFrame(
            self.assignations
            + list(dict(zip(self.no_pc["MATRICOLA"], ["NoPC"] * len(self.no_pc))))
        )
        all_bookings = pl.concat([self.no_pc, self.on_site])
        all_bookings = all_bookings.join(assignation, on="MATRICOLA", how="left")
        all_bookings.write_csv(path)
