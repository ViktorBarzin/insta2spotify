import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	if (event.url.pathname.startsWith('/api')) {
		const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
		const targetUrl = `${backendUrl}${event.url.pathname}${event.url.search}`;

		try {
			const headers: Record<string, string> = {};
			for (const name of ['content-type', 'x-api-key', 'authorization', 'accept']) {
				const value = event.request.headers.get(name);
				if (value) headers[name] = value;
			}

			let body: string | undefined;
			if (event.request.method !== 'GET' && event.request.method !== 'HEAD') {
				body = await event.request.text();
			}

			const response = await fetch(targetUrl, {
				method: event.request.method,
				headers,
				body,
				redirect: 'manual',
			});

			const responseHeaders = new Headers();
			response.headers.forEach((value, key) => {
				if (key.toLowerCase() !== 'transfer-encoding') {
					responseHeaders.set(key, value);
				}
			});

			const responseBody = await response.text();
			return new Response(responseBody, {
				status: response.status,
				headers: responseHeaders,
			});
		} catch (err) {
			console.error('API proxy error:', err);
			return new Response(JSON.stringify({ error: 'Proxy error', detail: String(err) }), {
				status: 502,
				headers: { 'content-type': 'application/json' },
			});
		}
	}
	return resolve(event);
};
