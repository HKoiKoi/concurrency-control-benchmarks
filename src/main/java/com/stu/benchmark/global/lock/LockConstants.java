package com.stu.benchmark.global.lock;

public final class LockConstants {

	private LockConstants() {
		throw new AssertionError("상수 전용 클래스입니다.");
	}

	/**
	 * 시스템 최대 처리 한계치 (mu)
	 * 최고 Peak TPS 기준 (223.89 req/s)
	 */
	public static final double SYSTEM_CAPACITY_MU = 223.89;

	// 큐잉 이론 임계치
	public static final double RHO_THRESHOLD_LOW = 0.24;
	public static final double RHO_THRESHOLD_HIGH = 0.34;
}
