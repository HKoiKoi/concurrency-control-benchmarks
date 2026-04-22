package com.stu.benchmark.global.lock;

import java.util.concurrent.TimeUnit;

public interface DistributedLock {

	/**
	 * 락 획득 시도 메서드
	 *
	 * @param key 락의 식별자 (LockType.generateKey()를 통해 생성된 키)
	 * @param waitTime 락 획득을 위해 대기할 최대 시간
	 * @param leaseTime 락 획득 후 자동으로 해제될 시간 (데드락 방지용)
	 * @param unit 시간 단위 (보통 TimeUnit.MILLISECONDS 사용)
	 * @return 락 획득 성공 여부
	 * @throws Exception Zookeeper 등 미들웨어 통신 중 발생할 수 있는 예외 처리를 위해 선언
	 */
	boolean tryLock(String key, long waitTime, long leaseTime, TimeUnit unit) throws Exception;

	/**
	 * 점유 락 해제 메서드
	 *
	 * @param key 해제할 락의 식별자
	 */
	void unlock(String key);

	/**
	 * 락 타입 반환 메서드
	 *
	 * @return PESSIMISTIC, REDISSON, ZOOKEEPER 중 하나
	 */
	LockType getLockType();
}
