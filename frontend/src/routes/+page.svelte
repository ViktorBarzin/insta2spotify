<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import '../app.css';

	interface SongResult {
		song: string;
		artist: string;
		method: string;
		spotify_url: string | null;
		added_to_playlist: boolean;
	}

	interface HistoryItem {
		id: number;
		instagram_url: string;
		status: string;
		created_at: string;
		songs: SongResult[];
	}

	let items: HistoryItem[] = $state([]);
	let loading = $state(true);
	let error = $state('');
	let timer: ReturnType<typeof setInterval>;

	async function fetchHistory() {
		try {
			const res = await fetch('/api/history?limit=50');
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const data = await res.json();
			items = data.items;
			error = '';
		} catch (e: any) {
			error = e.message || 'Failed to load history';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		fetchHistory();
		timer = setInterval(fetchHistory, 30000);
	});

	onDestroy(() => {
		if (timer) clearInterval(timer);
	});

	function statusBadge(status: string): string {
		switch (status) {
			case 'success': return 'bg-green-100 text-green-800';
			case 'partial': return 'bg-yellow-100 text-yellow-800';
			case 'processing': return 'bg-blue-100 text-blue-800';
			case 'error': return 'bg-red-100 text-red-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}

	function methodBadge(method: string): string {
		switch (method) {
			case 'metadata': return 'bg-purple-100 text-purple-800';
			case 'shazam': return 'bg-blue-100 text-blue-800';
			case 'ocr': return 'bg-orange-100 text-orange-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleString();
	}

	function shortenUrl(url: string): string {
		try {
			const u = new URL(url);
			return u.pathname.slice(0, 30) + (u.pathname.length > 30 ? '...' : '');
		} catch {
			return url.slice(0, 30);
		}
	}
</script>

<svelte:head>
	<title>insta2spotify</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
	<header class="bg-white shadow-sm border-b border-gray-200">
		<div class="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-gray-900">insta2spotify</h1>
				<p class="text-sm text-gray-500">Instagram Reels to Spotify Playlist</p>
			</div>
			<a href="https://open.spotify.com/playlist/7lcLakPy8pwwegFoOQ7MoG"
				target="_blank" rel="noopener"
				class="text-green-600 hover:text-green-700 font-medium text-sm">
				Open Playlist
			</a>
		</div>
	</header>

	<main class="max-w-6xl mx-auto px-4 py-6">
		{#if loading}
			<div class="text-center py-20 text-gray-500">Loading history...</div>
		{:else if error}
			<div class="text-center py-20">
				<p class="text-red-500 mb-4">{error}</p>
				<button onclick={fetchHistory}
					class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
					Retry
				</button>
			</div>
		{:else if items.length === 0}
			<div class="text-center py-20 text-gray-500">
				<p class="text-lg mb-2">No songs identified yet</p>
				<p class="text-sm">Share an Instagram reel via the iOS Shortcut to get started</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each items as item (item.id)}
					<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
						<div class="flex items-center justify-between mb-3">
							<div class="flex items-center gap-3">
								<span class="text-sm {statusBadge(item.status)} px-2 py-0.5 rounded-full font-medium">
									{item.status}
								</span>
								<a href={item.instagram_url} target="_blank" rel="noopener"
									class="text-sm text-blue-600 hover:underline">
									{shortenUrl(item.instagram_url)}
								</a>
							</div>
							<span class="text-xs text-gray-400">{formatDate(item.created_at)}</span>
						</div>
						{#if item.songs.length > 0}
							<div class="divide-y divide-gray-100">
								{#each item.songs as song}
									<div class="py-2 flex items-center justify-between">
										<div class="flex items-center gap-3">
											<span class="text-xs {methodBadge(song.method)} px-1.5 py-0.5 rounded font-medium">
												{song.method}
											</span>
											<span class="font-medium text-gray-900">{song.song}</span>
											<span class="text-gray-500">by {song.artist}</span>
										</div>
										<div class="flex items-center gap-2">
											{#if song.added_to_playlist}
												<span class="text-green-600 text-xs font-medium">Added</span>
											{/if}
											{#if song.spotify_url}
												<a href={song.spotify_url} target="_blank" rel="noopener"
													class="text-green-600 hover:text-green-700 text-sm">
													Spotify
												</a>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<p class="text-sm text-gray-400">No songs identified</p>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</main>
</div>
