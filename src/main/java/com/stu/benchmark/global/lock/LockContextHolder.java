package com.stu.benchmark.global.lock;

/**
 * AOP에서 결정된 락 전략을 서비스 레이어에 전달하기 위한 컨텍스트 홀더
 */
public class LockContextHolder {

	private static final ThreadLocal<LockType> CONTEXT = new ThreadLocal<>();

	public static void set(LockType lockType) {
		CONTEXT.set(lockType);
	}

	public static LockType get() {
		return CONTEXT.get();
	}

	public static void clear() {
		CONTEXT.remove();
	}
}
