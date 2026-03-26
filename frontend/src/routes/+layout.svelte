<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { isLoggedIn, getUsername, logout } from '$lib/api';

	let { children } = $props();
	let loggedIn = $state(false);
	let username = $state('');
	let currentPath = $state('');

	onMount(() => {
		checkAuth();
	});

	$effect(() => {
		currentPath = $page.url.pathname;
		checkAuth();
	});

	function checkAuth() {
		loggedIn = isLoggedIn();
		username = getUsername() || '';
		if (!loggedIn && currentPath !== '/login') {
			goto('/login');
		}
	}

	function handleLogout() {
		logout();
		goto('/login');
	}
</script>

{#if currentPath === '/login'}
	{@render children()}
{:else if loggedIn}
	<div class="app">
		<header>
			<nav>
				<a href="/" class="logo">⚙ WeldCheck</a>
				<div class="nav-right">
					<a href="/history" class="nav-link" class:active={currentPath === '/history'}>이력</a>
					<span class="user-badge">{username}</span>
					<button class="logout-btn" onclick={handleLogout}>로그아웃</button>
				</div>
			</nav>
		</header>
		<main>
			{@render children()}
		</main>
	</div>
{/if}

<style>
	.app {
		min-height: 100dvh;
		display: flex;
		flex-direction: column;
	}
	header {
		background: var(--primary);
		color: white;
		padding: 0.625rem 1rem;
		position: sticky;
		top: 0;
		z-index: 100;
		box-shadow: 0 2px 8px rgba(0,0,0,0.15);
	}
	nav {
		display: flex;
		align-items: center;
		justify-content: space-between;
		max-width: 960px;
		margin: 0 auto;
	}
	nav a {
		color: white;
		text-decoration: none;
	}
	.logo {
		font-size: 1.1rem;
		font-weight: 700;
	}
	.nav-right {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.nav-link {
		padding: 0.25rem 0.625rem;
		border-radius: 0.375rem;
		font-size: 0.85rem;
		font-weight: 600;
		transition: background 0.2s;
	}
	.nav-link:hover, .nav-link.active {
		background: rgba(255,255,255,0.2);
	}
	.user-badge {
		font-size: 0.75rem;
		background: rgba(255,255,255,0.2);
		padding: 0.2rem 0.5rem;
		border-radius: 1rem;
	}
	.logout-btn {
		background: rgba(255,255,255,0.15);
		border: 1px solid rgba(255,255,255,0.3);
		color: white;
		padding: 0.25rem 0.5rem;
		border-radius: 0.375rem;
		font-size: 0.75rem;
		cursor: pointer;
	}
	main {
		flex: 1;
		max-width: 960px;
		margin: 0 auto;
		width: 100%;
		padding: 1rem;
	}

	@media (max-width: 480px) {
		.logo {
			font-size: 0.95rem;
		}
		.nav-right {
			gap: 0.375rem;
		}
		.user-badge {
			display: none;
		}
	}
</style>
