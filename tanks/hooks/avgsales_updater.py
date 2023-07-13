from datetime import timedelta

from sqlmodel import Session, col

from tanks.models import AverageSale
from tanks.schemas import Sale


class AvgSalesUpdater:
    window_weeks = 5

    def __init__(self, session: Session):
        self._session = session

    def _affected_avg_sales(self, sale: Sale) -> list[AverageSale]:
        date = sale.created_at.date()
        affected_dates = [
            date + timedelta(weeks=weeks) for weeks in range(self.window_weeks)
        ]
        query = (
            self._session.query(AverageSale)
            .filter_by(tank_id=sale.tank_id)
            .filter(col(AverageSale.date).in_(affected_dates))
        )
        result = query.all()

        if not result:
            return [
                AverageSale(id=None, tank_id=sale.tank_id, date=date, sales=0, total=0)
                for date in affected_dates
            ]

        return result

    def handle_added_sale(self, sale: Sale) -> None:
        if sale.quantity <= 0:
            raise ValueError(
                f"Expected positive sale.quantity. Received {sale.quantity}."
            )

        for entry in self._affected_avg_sales(sale):
            entry.sales += 1
            entry.total += sale.quantity

            self._session.add(entry)

        self._session.commit()

    def _violates_invariant(self, sales: int, total: float) -> bool:
        return total < 0.0 or ((sales == 0 or total == 0.0) and sales != total)

    def handle_deleted_sale(self, sale: Sale) -> None:
        if sale.quantity <= 0:
            raise ValueError("Expected non-zero positive sale.quantity.")

        affected_avg_sales = self._affected_avg_sales(sale)

        for entry in affected_avg_sales:
            if self._violates_invariant(
                sales=entry.sales - 1,
                total=entry.total - sale.quantity,
            ):
                raise ValueError(
                    f"Deleting {sale} is inconsistent with the existing {entry}."
                )

        for entry in affected_avg_sales:
            entry.sales -= 1
            entry.total -= sale.quantity

            if entry.total == 0.0:
                self._session.delete(entry)
                continue

        self._session.commit()
