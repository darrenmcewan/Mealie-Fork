import { BaseCRUDAPI } from "../base/base-clients";
import { route } from "../base/route";
import type { CreatePlanEntry, CreateRandomEntry, LeftoverPlanEntryPagination, ReadPlanEntry, UpdatePlanEntry } from "~/lib/api/types/meal-plan";

const prefix = "/api";

const routes = {
  mealplan: `${prefix}/households/mealplans`,
  random: `${prefix}/households/mealplans/random`,
  mealplanId: (id: string | number) => `${prefix}/households/mealplans/${id}`,
};

export class MealPlanAPI extends BaseCRUDAPI<CreatePlanEntry, ReadPlanEntry, UpdatePlanEntry> {
  baseRoute = routes.mealplan;
  itemRoute = routes.mealplanId;

  async setRandom(payload: CreateRandomEntry) {
    return await this.requests.post<ReadPlanEntry>(routes.random, payload);
  }

  async getLeftovers(targetDate: string, editingEntryId?: number, page = 1, perPage = 20, sourceId?: number) {
    return await this.requests.get<LeftoverPlanEntryPagination>(route(`${routes.mealplan}/leftovers`, {
      target_date: targetDate,
      ...(editingEntryId == null ? {} : { editing_entry_id: editingEntryId }),
      ...(sourceId == null ? {} : { queryFilter: `id = ${sourceId}` }),
      page,
      perPage,
    }));
  }
}
