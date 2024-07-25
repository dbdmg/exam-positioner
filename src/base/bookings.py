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
        return (
            self.dsa.height
            + self.no_pc.height
            + self.on_site.height
            - len(self.assignations)
        )

    def save_assignations(self, path: str):
        self.assignation |= dict(
            zip(self.no_pc["MATRICOLA"], ["NoPC"] * len(self.no_pc))
        )
        self.assignation = pl.DataFrame(self.assignations)
        all_bookings = pl.concat([self.dsa, self.no_pc, self.on_site])
        all_bookings = all_bookings.join(self.assignation, on="MATRICOLA", how="left")
        all_bookings.write_csv(path)
