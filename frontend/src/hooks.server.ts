import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	if (event.url.pathname.startsWith('/api')) {
		const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
		const targetUrl = `${backendUrl}${event.url.pathname}${event.url.search}`;
		const response = await fetch(targetUrl, {
			method: event.request.method,
			headers: event.request.headers,
			body: event.request.method !== 'GET' ? await event.request.text() : undefined,
			redirect: 'manual',
		});
		return new Response(response.body, {
			status: response.status,
			headers: response.headers,
		});
	}
	return resolve(event);
};
