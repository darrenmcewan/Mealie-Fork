from typing import Annotated

from fastapi import Query, Response

from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.user.cooking_insights import CookingInsightsQuery, CookingInsightsResponse
from mealie.services.recipe.cooking_insights_service import CookingInsightsService

router = UserAPIRouter(prefix="/users", tags=["Users: Cooking Insights"])


@controller(router)
class CookingInsightsController(BaseUserController):
    @router.get("/self/cooking-insights", response_model=CookingInsightsResponse)
    def get_cooking_insights(self, query: Annotated[CookingInsightsQuery, Query()], response: Response):
        response.headers["Cache-Control"] = "private, no-store"
        return CookingInsightsService(self.repos.cooking_history, self.user.id).get(query)
