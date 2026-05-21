from dependency_injector import containers, providers

from src.core.config import configs
from src.core.database import Database
from src.services.clinical_assistant_service import ClinicalAssistantService
from src.services.llm_caching_service import LLMCacheService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["src.api.endpoints.clinical", "src.api.endpoints.demo"]
    )
    db = providers.Singleton(Database, db_url=configs.DATABASE_URI)
    db_session = providers.Singleton(db.provided.session)

    llm_cache_service = providers.Factory(LLMCacheService, db_session=db_session)
    clinical_assistant_service = providers.Factory(ClinicalAssistantService, llm_cache_service=llm_cache_service)
