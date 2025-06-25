export async function cleanData(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch('/api/clean', {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error('Failed to clean data');
  }

  return res.json();
}
