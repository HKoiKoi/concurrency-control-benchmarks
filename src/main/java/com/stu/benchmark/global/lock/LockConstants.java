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

	// Th1: Pessimistic <-> Zookeeper 전환 기준 (중심값: 0.24)
	public static final double RHO_TH1_UP = 0.24;
	public static final double RHO_TH1_DOWN = 0.22;

	// Th2: Zookeeper <-> Redisson 전환 기준 (중심값: 0.34)
	public static final double RHO_TH2_UP = 0.34;
	public static final double RHO_TH2_DOWN = 0.32;
}
