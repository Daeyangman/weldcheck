<script lang="ts">
	import { login } from '$lib/api';
	import { goto } from '$app/navigation';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleLogin(e: Event) {
		e.preventDefault();
		if (!username || !password) return;
		loading = true;
		error = '';
		try {
			await login(username, password);
			goto('/');
		} catch (err: any) {
			error = err.message;
		} finally {
			loading = false;
		}
	}
</script>

<section class="login-page">
	<div class="login-card">
		<div class="login-header">
			<span class="login-icon">⚙</span>
			<h1>WeldCheck</h1>
			<p>용접 품질 검사 시스템</p>
		</div>

		<form onsubmit={handleLogin}>
			<div class="field">
				<label for="username">이름 (ID)</label>
				<input
					id="username"
					type="text"
					bind:value={username}
					placeholder="이름을 입력하세요"
					autocomplete="username"
				/>
			</div>
			<div class="field">
				<label for="password">비밀번호</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					placeholder="비밀번호를 입력하세요"
					autocomplete="current-password"
				/>
			</div>

			{#if error}
				<div class="alert error">{error}</div>
			{/if}

			<button type="submit" class="btn primary" disabled={loading || !username || !password}>
				{loading ? '로그인 중...' : '로그인'}
			</button>
		</form>
	</div>
</section>

<style>
	.login-page {
		min-height: 100dvh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;
		background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
	}
	.login-card {
		background: white;
		border-radius: 1rem;
		padding: 2rem;
		width: 100%;
		max-width: 400px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
	}
	.login-header {
		text-align: center;
		margin-bottom: 1.5rem;
	}
	.login-icon {
		font-size: 2.5rem;
	}
	.login-header h1 {
		font-size: 1.5rem;
		margin-top: 0.5rem;
		color: var(--text);
	}
	.login-header p {
		color: var(--text-secondary);
		font-size: 0.875rem;
		margin-top: 0.25rem;
	}
	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	.field {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	.field label {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-secondary);
	}
	.field input {
		padding: 0.75rem;
		border: 1px solid var(--border);
		border-radius: 0.5rem;
		font-size: 1rem;
		outline: none;
		transition: border-color 0.2s;
	}
	.field input:focus {
		border-color: var(--primary);
	}
	.alert.error {
		padding: 0.625rem 0.75rem;
		background: #fef2f2;
		color: #dc2626;
		border-radius: 0.5rem;
		font-size: 0.875rem;
	}
	.btn.primary {
		padding: 0.75rem;
		background: var(--primary);
		color: white;
		border: none;
		border-radius: 0.5rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}
	.btn.primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
