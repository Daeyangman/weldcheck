<script lang="ts">
	import { getHistory, getImage } from '$lib/api';
	import { onMount } from 'svelte';

	let records: any[] = $state([]);
	let loading = $state(true);
	let error = $state('');
	let expandedId: number | null = $state(null);

	onMount(async () => {
		try {
			records = await getHistory();
		} catch {
			error = '이력을 불러올 수 없습니다.';
		} finally {
			loading = false;
		}
	});

	function toggle(id: number) {
		expandedId = expandedId === id ? null : id;
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleString('ko-KR', {
			month: 'short', day: 'numeric',
			hour: '2-digit', minute: '2-digit'
		});
	}
</script>

<section class="history-page">
	<h1>검사 이력</h1>

	{#if loading}
		<p class="loading">불러오는 중...</p>
	{:else if error}
		<div class="alert error">{error}</div>
	{:else if records.length === 0}
		<div class="alert info">검사 이력이 없습니다.</div>
	{:else}
		<div class="record-list">
			{#each records as rec}
				<div class="record-card" onclick={() => toggle(rec.id)} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && toggle(rec.id)}>
					<div class="record-summary">
						<div class="record-info">
							<span class="record-date">{formatDate(rec.created_at)}</span>
							<span class="record-user">{rec.user_name}</span>
							<span class="record-model">{rec.model_name}</span>
						</div>
						<div class="record-badges">
							{#if rec.pass_count > 0}
								<span class="mini-badge pass">PASS {rec.pass_count}</span>
							{/if}
							{#if rec.fail_count > 0}
								<span class="mini-badge fail">FAIL {rec.fail_count}</span>
							{/if}
						</div>
					</div>

					{#if expandedId === rec.id}
						<div class="record-detail">
							<img src={getImage(rec.original_path)} alt="원본" class="original-img" />
							{#if rec.detections}
								{#each rec.detections as det, i}
									<div class="det-row">
										<img src={getImage(det.crop_path)} alt="검출 {i+1}" class="det-img" />
										<div class="det-info">
											<span class="badge {det.judgment}">{det.judgment}</span>
											<span>{det.class_name}</span>
											<span class="conf">{(det.confidence * 100).toFixed(1)}%</span>
										</div>
									</div>
								{/each}
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</section>

<style>
	.history-page {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	h1 {
		font-size: 1.5rem;
		font-weight: 700;
	}
	.loading {
		text-align: center;
		color: var(--text-secondary);
		padding: 2rem;
	}
	.alert {
		padding: 0.75rem 1rem;
		border-radius: 0.5rem;
	}
	.alert.error { background: #fef2f2; color: var(--danger); }
	.alert.info { background: #eff6ff; color: var(--primary); }
	.record-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.record-card {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 0.75rem;
		padding: 0.75rem 1rem;
		cursor: pointer;
	}
	.record-summary {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.record-info {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}
	.record-date {
		font-weight: 600;
		font-size: 0.9rem;
	}
	.record-user {
		font-size: 0.8rem;
		color: var(--primary);
		font-weight: 600;
	}
	.record-model {
		font-size: 0.75rem;
		color: var(--text-secondary);
	}
	.record-badges {
		display: flex;
		gap: 0.375rem;
	}
	.mini-badge {
		padding: 0.125rem 0.5rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 700;
	}
	.mini-badge.pass { background: #dcfce7; color: var(--success); }
	.mini-badge.fail { background: #fef2f2; color: var(--danger); }
	.record-detail {
		margin-top: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.original-img {
		width: 100%;
		border-radius: 0.5rem;
	}
	.det-row {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		padding: 0.5rem;
		background: var(--bg);
		border-radius: 0.5rem;
	}
	.det-img {
		width: 80px;
		height: 80px;
		object-fit: cover;
		border-radius: 0.375rem;
	}
	.det-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		font-size: 0.85rem;
	}
	.badge {
		display: inline-block;
		width: fit-content;
		padding: 0.125rem 0.5rem;
		border-radius: 1rem;
		font-weight: 700;
		font-size: 0.75rem;
	}
	.badge.PASS { background: #dcfce7; color: var(--success); }
	.badge.FAIL { background: #fef2f2; color: var(--danger); }
	.conf {
		color: var(--text-secondary);
		font-size: 0.75rem;
	}
	@media (min-width: 768px) {
		.record-list {
			display: grid;
			grid-template-columns: repeat(2, 1fr);
		}
	}
	@media (min-width: 1024px) {
		.record-list {
			grid-template-columns: repeat(3, 1fr);
		}
	}
</style>
