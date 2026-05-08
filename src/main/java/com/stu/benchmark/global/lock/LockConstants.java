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

	// 상향 임계점 (과부하 방어 임계점: 0.24)
	public static final double RHO_TH1_UP = 0.24;

	// 하향 임계점 (안정화 복귀 임계점: 0.22)
	public static final double RHO_TH1_DOWN = 0.22;
}
