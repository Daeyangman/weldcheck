<script lang="ts">
	import { getModels, inspect, getImage, getUsername } from '$lib/api';
	import { onMount } from 'svelte';

	let models: string[] = $state([]);
	let selectedModel = $state('');
	let file: File | null = $state(null);
	let preview = $state('');
	let loading = $state(false);
	let result: any = $state(null);
	let error = $state('');
	let fileInput: HTMLInputElement;

	onMount(async () => {
		try {
			models = await getModels();
			if (models.length > 0) selectedModel = models[0];
		} catch {
			error = '서버에 연결할 수 없습니다.';
		}
	});

	function handleFile(e: Event) {
		const target = e.target as HTMLInputElement;
		const f = target.files?.[0];
		if (!f) return;
		file = f;
		result = null;
		error = '';
		const reader = new FileReader();
		reader.onload = () => { preview = reader.result as string; };
		reader.readAsDataURL(f);
	}

	async function runInspection() {
		if (!file || !selectedModel) return;
		loading = true;
		error = '';
		result = null;
		try {
			result = await inspect(file, selectedModel);
		} catch {
			error = '검사 중 오류가 발생했습니다.';
		} finally {
			loading = false;
		}
	}

	function reset() {
		file = null;
		preview = '';
		result = null;
		error = '';
		if (fileInput) fileInput.value = '';
	}
</script>

<section class="inspect-page">
	<h1>용접 검사</h1>

	<div class="model-select">
		<label for="model">모델 선택</label>
		<select id="model" bind:value={selectedModel}>
			{#each models as m}
				<option value={m}>{m}</option>
			{/each}
		</select>
	</div>

	<div class="upload-area" onclick={() => fileInput.click()} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && fileInput.click()}>
		{#if preview}
			<img src={preview} alt="미리보기" class="preview-img" />
		{:else}
			<div class="upload-placeholder">
				<span class="upload-icon">📷</span>
				<p>이미지 또는 영상을 선택하세요</p>
				<p class="hint">탭하여 파일 선택</p>
			</div>
		{/if}
		<input
			bind:this={fileInput}
			type="file"
			accept="image/*,video/*"
			capture="environment"
			onchange={handleFile}
			hidden
		/>
	</div>

	{#if file}
		<div class="actions">
			<button class="btn primary" onclick={runInspection} disabled={loading || !selectedModel}>
				{loading ? '검사 중...' : '검사 시작'}
			</button>
			<button class="btn secondary" onclick={reset} disabled={loading}>초기화</button>
		</div>
	{/if}

	{#if error}
		<div class="alert error">{error}</div>
	{/if}

	{#if result}
		<div class="results">
			<h2>검사 결과</h2>
			{#if result.detections && result.detections.length > 0}
				{#each result.detections as det, i}
					<div class="result-card {det.judgment}">
						<div class="result-header">
							<span class="badge {det.judgment}">{det.judgment}</span>
							<span class="confidence">{(det.confidence * 100).toFixed(1)}%</span>
						</div>
						<img src={getImage(det.crop_path)} alt="검출 {i + 1}" class="crop-img" />
						<p class="label">{det.class_name}</p>
					</div>
				{/each}
			{:else}
				<div class="alert info">용접 부위가 검출되지 않았습니다.</div>
			{/if}
		</div>
	{/if}
</section>

<style>
	.inspect-page {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	h1 {
		font-size: 1.5rem;
		font-weight: 700;
	}
	.model-select {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	.model-select label {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-secondary);
	}
	.model-select select {
		padding: 0.625rem;
		border: 1px solid var(--border);
		border-radius: 0.5rem;
		font-size: 1rem;
		background: var(--card);
	}
	.upload-area {
		border: 2px dashed var(--border);
		border-radius: 0.75rem;
		padding: 2rem;
		text-align: center;
		cursor: pointer;
		background: var(--card);
		transition: border-color 0.2s;
	}
	.upload-area:hover, .upload-area:focus {
		border-color: var(--primary);
	}
	.upload-placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}
	.upload-icon {
		font-size: 2.5rem;
	}
	.hint {
		font-size: 0.8rem;
		color: var(--text-secondary);
	}
	.preview-img {
		max-width: 100%;
		max-height: 300px;
		border-radius: 0.5rem;
		object-fit: contain;
	}
	.actions {
		display: flex;
		gap: 0.75rem;
	}
	.btn {
		flex: 1;
		padding: 0.75rem;
		border: none;
		border-radius: 0.5rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}
	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.btn.primary {
		background: var(--primary);
		color: white;
	}
	.btn.secondary {
		background: var(--border);
		color: var(--text);
	}
	.alert {
		padding: 0.75rem 1rem;
		border-radius: 0.5rem;
		font-size: 0.9rem;
	}
	.alert.error {
		background: #fef2f2;
		color: var(--danger);
	}
	.alert.info {
		background: #eff6ff;
		color: var(--primary);
	}
	.results {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	h2 {
		font-size: 1.2rem;
		font-weight: 700;
	}
	.result-card {
		background: var(--card);
		border-radius: 0.75rem;
		padding: 1rem;
		border: 2px solid var(--border);
	}
	.result-card.PASS {
		border-color: var(--success);
	}
	.result-card.FAIL {
		border-color: var(--danger);
	}
	.result-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}
	.badge {
		padding: 0.25rem 0.75rem;
		border-radius: 1rem;
		font-weight: 700;
		font-size: 0.875rem;
	}
	.badge.PASS {
		background: #dcfce7;
		color: var(--success);
	}
	.badge.FAIL {
		background: #fef2f2;
		color: var(--danger);
	}
	.confidence {
		font-size: 0.875rem;
		color: var(--text-secondary);
	}
	.crop-img {
		width: 100%;
		border-radius: 0.5rem;
		margin-bottom: 0.5rem;
	}
	.label {
		font-size: 0.875rem;
		color: var(--text-secondary);
	}
	@media (min-width: 768px) {
		.results {
			display: grid;
			grid-template-columns: repeat(2, 1fr);
			gap: 1rem;
		}
		h2 {
			grid-column: 1 / -1;
		}
	}
	@media (min-width: 1024px) {
		.results {
			grid-template-columns: repeat(3, 1fr);
		}
	}
</style>
