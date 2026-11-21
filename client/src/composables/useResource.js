import { onBeforeMount, ref, watch } from "vue";
import axios from "axios";

/**
 * Общая логика CRUD для одной модели:
 * загрузка списка и статистики с фильтрами, создание, изменение, удаление, ссылка на экспорт.
 *
 * url — адрес ViewSet, например "/api/students/"
 * initialFilters — фильтры по колонкам, например { last_name: "", year_of_study: "" }
 */
export function useResource(url, initialFilters = {}) {
  const items = ref([]);
  const stats = ref([]);
  const loading = ref(false);
  const filters = ref({ ...initialFilters, user: "" });

  // только заполненные фильтры уходят на сервер
  function activeFilters() {
    return Object.fromEntries(
      Object.entries(filters.value).filter(([, value]) => value !== "" && value !== null && value !== undefined),
    );
  }

  async function fetchItems() {
    loading.value = true;
    try {
      const params = activeFilters();
      const [list, stat] = await Promise.all([
        axios.get(url, { params }),
        axios.get(`${url}stats/`, { params }),
      ]);
      items.value = list.data;
      stats.value = stat.data;
    } finally {
      loading.value = false;
    }
  }

  // при изменении фильтра перезагружаем данные (с небольшой задержкой, пока пользователь печатает)
  let timer;
  watch(
    filters,
    () => {
      clearTimeout(timer);
      timer = setTimeout(fetchItems, 300);
    },
    { deep: true },
  );

  async function create(data) {
    await axios.post(url, data);
    await fetchItems(); // reload
  }

  async function update(id, data) {
    await axios.patch(`${url}${id}/`, data);
    await fetchItems(); // reload
  }

  async function remove(id) {
    await axios.delete(`${url}${id}/`);
    await fetchItems(); // reload
  }

  // ссылка на выгрузку в Excel/Word с текущими фильтрами
  function exportUrl(type) {
    const query = new URLSearchParams({ ...activeFilters(), type });
    return `${url}export/?${query}`;
  }

  function resetFilters() {
    filters.value = { ...initialFilters, user: "" };
  }

  onBeforeMount(fetchItems);

  return { items, stats, loading, filters, fetchItems, create, update, remove, exportUrl, resetFilters };
}

/** Список объектов для выпадающих списков (кафедры, преподаватели и т.д.) */
export function useOptions(url) {
  const options = ref([]);
  async function load() {
    const r = await axios.get(url);
    options.value = r.data;
  }
  onBeforeMount(load);
  return { options, reload: load };
}
