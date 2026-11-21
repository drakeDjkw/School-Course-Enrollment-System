/**
 * Собирает FormData для отправки вместе с файлом.
 * data  — обычные поля ({ first_name: "...", year_of_study: 2 })
 * files — файлы ({ picture: File }); пустые значения пропускаются,
 *         поэтому при редактировании без нового файла старая картинка остаётся.
 */
export function toFormData(data, files = {}) {
  const formData = new FormData();
  for (const [key, value] of Object.entries(data)) {
    if (value === null || value === undefined) continue;
    formData.append(key, value);
  }
  for (const [key, file] of Object.entries(files)) {
    if (file) formData.append(key, file);
  }
  return formData;
}
