from src.app.repositories.payment_repository import PaymentRepository
from src.app.services.payment_service import PaymentService
from src.app.conf import db_manager


async def get_payment_service():
    async with db_manager.session() as session:
        repository = PaymentRepository(session)
        yield PaymentService(session=session, repository=repository)
