package com.stu.benchmark.global.lock.strategy;

import java.util.concurrent.TimeUnit;

import org.springframework.stereotype.Component;

import com.stu.benchmark.global.lock.DistributedLock;
import com.stu.benchmark.global.lock.LockType;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
public class PessimisticLockStrategy implements DistributedLock {

	@Override
	public boolean tryLock(String key, long waitTime, long leaseTime, TimeUnit unit) {

		// 비관적 락은 DB 트랜잭션 내부에서 Repository 메서드 호출 시점에 물리적 락 걸림
		// 따라서 미들웨어 락과 인터페이스 규격을 맞추기 위해 락 획득 성공만 반환
		log.debug("[Pessimistic Lock] 비관적 락 전략이 선택되었습니다. 트랜잭션 내부에서 락이 제어됩니다.");
		return true;
	}

	@Override
	public void unlock(String key) {
		// 비관적 락은 DB 트랜잭션 종료 시점에 자동으로 해제됩니다.
		// 애플리케이션 레벨에서 명시적으로 해제할 필요가 없습니다.
	}

	@Override
	public LockType getLockType() {
		return LockType.PESSIMISTIC;
	}
}
