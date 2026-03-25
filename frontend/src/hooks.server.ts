import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	if (event.url.pathname.startsWith('/api')) {
		const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
		const targetUrl = `${backendUrl}${event.url.pathname}${event.url.search}`;

		const headers: Record<string, string> = {};
		const forwardHeaders = ['content-type', 'x-api-key', 'authorization', 'accept'];
		for (const name of forwardHeaders) {
			const value = event.request.headers.get(name);
			if (value) headers[name] = value;
		}

		const init: RequestInit = {
			method: event.request.method,
			headers,
			redirect: 'manual',
		};

		if (event.request.method !== 'GET' && event.request.method !== 'HEAD') {
			init.body = await event.request.text();
		}

		const response = await fetch(targetUrl, init);
		return new Response(response.body, {
			status: response.status,
			headers: response.headers,
		});
	}
	return resolve(event);
};
