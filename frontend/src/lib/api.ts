const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getToken(): string | null {
	if (typeof window === 'undefined') return null;
	return localStorage.getItem('token');
}

function authHeaders(): Record<string, string> {
	const token = getToken();
	return token ? { Authorization: `Bearer ${token}` } : {};
}

export function isLoggedIn(): boolean {
	return !!getToken();
}

export function getUsername(): string | null {
	if (typeof window === 'undefined') return null;
	return localStorage.getItem('username');
}

export async function login(username: string, password: string): Promise<{ token: string; username: string }> {
	const res = await fetch(`${API_BASE}/login`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ username, password })
	});
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail || '로그인 실패');
	}
	const data = await res.json();
	localStorage.setItem('token', data.token);
	localStorage.setItem('username', data.username);
	return data;
}

export function logout() {
	localStorage.removeItem('token');
	localStorage.removeItem('username');
}

export async function getModels(): Promise<string[]> {
	const res = await fetch(`${API_BASE}/models`);
	return res.json();
}

export async function inspect(file: File, model: string): Promise<any> {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('model', model);
	const res = await fetch(`${API_BASE}/inspect`, {
		method: 'POST',
		headers: authHeaders(),
		body: formData
	});
	if (res.status === 401) {
		logout();
		window.location.href = '/login';
		throw new Error('인증이 만료되었습니다');
	}
	return res.json();
}

export async function getHistory(): Promise<any[]> {
	const res = await fetch(`${API_BASE}/history`);
	return res.json();
}

export function getImage(path: string): string {
	return `${API_BASE}/files/${encodeURIComponent(path)}`;
}
