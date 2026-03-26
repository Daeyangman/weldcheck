<script lang="ts">
	import { getModels, inspect, getImage, getUsername } from '$lib/api';
	import { onMount } from 'svelte';

	let models: string[] = $state([]);
	let selectedModel = $state('');
	let files: File[] = $state([]);
	let previews: string[] = $state([]);
	let loading = $state(false);
	let results: any[] = $state([]);
	let progress = $state('');
	let error = $state('');
	let cameraInput: HTMLInputElement;
	let galleryInput: HTMLInputElement;

	onMount(async () => {
		try {
			models = await getModels();
			if (models.length > 0) selectedModel = models[0];
		} catch {
			error = '서버에 연결할 수 없습니다.';
		}
	});

	function handleFiles(e: Event) {
		const target = e.target as HTMLInputElement;
		const selected = target.files;
		if (!selected || selected.length === 0) return;
		const newFiles = Array.from(selected);
		files = [...files, ...newFiles];
		results = [];
		error = '';
		for (const f of newFiles) {
			const reader = new FileReader();
			reader.onload = () => { previews = [...previews, reader.result as string]; };
			reader.readAsDataURL(f);
		}
	}

	function removeFile(index: number) {
		files = files.filter((_, i) => i !== index);
		previews = previews.filter((_, i) => i !== index);
	}

	async function runInspection() {
		if (files.length === 0 || !selectedModel) return;
		loading = true;
		error = '';
		results = [];
		for (let i = 0; i < files.length; i++) {
			progress = `검사 중... (${i + 1}/${files.length})`;
			try {
				const res = await inspect(files[i], selectedModel);
				results = [...results, { filename: files[i].name, preview: previews[i], ...res }];
			} catch {
				results = [...results, { filename: files[i].name, preview: previews[i], error: true }];
			}
		}
		progress = '';
		loading = false;
	}

	function reset() {
		files = [];
		previews = [];
		results = [];
		error = '';
		progress = '';
		if (cameraInput) cameraInput.value = '';
		if (galleryInput) galleryInput.value = '';
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

	<div class="upload-buttons">
		<button class="upload-btn" onclick={() => cameraInput.click()}>
			<span>📷</span> 카메라 촬영
		</button>
		<button class="upload-btn" onclick={() => galleryInput.click()}>
			<span>🖼</span> 갤러리 선택
		</button>
		<input
			bind:this={cameraInput}
			type="file"
			accept="image/*"
			capture="environment"
			onchange={handleFiles}
			hidden
		/>
		<input
			bind:this={galleryInput}
			type="file"
			accept="image/*,video/*"
			multiple
			onchange={handleFiles}
			hidden
		/>
	</div>

	{#if previews.length > 0}
		<div class="preview-grid">
			{#each previews as p, i}
				<div class="preview-item">
					<img src={p} alt="미리보기 {i + 1}" />
					<button class="remove-btn" onclick={() => removeFile(i)}>✕</button>
				</div>
			{/each}
		</div>
	{/if}

	{#if files.length > 0}
		<div class="actions">
			<button class="btn primary" onclick={runInspection} disabled={loading || !selectedModel}>
				{loading ? progress : `검사 시작 (${files.length}장)`}
			</button>
			<button class="btn secondary" onclick={reset} disabled={loading}>초기화</button>
		</div>
	{/if}

	{#if error}
		<div class="alert error">{error}</div>
	{/if}

	{#if results.length > 0}
		<div class="results">
			<h2>검사 결과 ({results.length}건)</h2>
			{#each results as res, ri}
				<div class="result-group">
					<p class="result-filename">{res.filename}</p>
					{#if res.error}
						<div class="alert error">검사 실패</div>
					{:else if res.detections && res.detections.length > 0}
						{#each res.detections as det, i}
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
			{/each}
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
	.upload-buttons {
		display: flex;
		gap: 0.75rem;
	}
	.upload-btn {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.375rem;
		padding: 1.25rem 0.5rem;
		border: 2px dashed var(--border);
		border-radius: 0.75rem;
		background: var(--card);
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--text);
		transition: border-color 0.2s;
	}
	.upload-btn:hover {
		border-color: var(--primary);
	}
	.upload-btn span {
		font-size: 1.75rem;
	}
	.preview-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.5rem;
	}
	.preview-item {
		position: relative;
		aspect-ratio: 1;
		border-radius: 0.5rem;
		overflow: hidden;
	}
	.preview-item img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.remove-btn {
		position: absolute;
		top: 4px;
		right: 4px;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		border: none;
		background: rgba(0,0,0,0.6);
		color: white;
		font-size: 0.75rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.result-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.result-filename {
		font-weight: 600;
		font-size: 0.85rem;
		color: var(--text-secondary);
		padding-top: 0.5rem;
		border-top: 1px solid var(--border);
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
