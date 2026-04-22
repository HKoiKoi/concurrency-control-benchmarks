package com.stu.benchmark.global.lock.strategy;

import java.util.concurrent.TimeUnit;

import org.apache.curator.framework.CuratorFramework;
import org.apache.curator.framework.recipes.locks.InterProcessMutex;
import org.springframework.stereotype.Component;

import com.stu.benchmark.global.lock.DistributedLock;
import com.stu.benchmark.global.lock.LockType;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class ZookeeperLockStrategy implements DistributedLock {

	private final CuratorFramework curatorFramework;
	private final ThreadLocal<InterProcessMutex> lockHolder = new ThreadLocal<>();

	@Override
	public boolean tryLock(String key, long waitTime, long leaseTime, TimeUnit unit) throws Exception {

		// InterProcessMutex는 자체적인 TTL(leaseTime)을 지원하지 않습니다.
		// 프로세스 비정상 종료 시 Zookeeper 세션 만료(session timeout)로 락이 자동 해제됩니다.
		InterProcessMutex mutex = new InterProcessMutex(curatorFramework, key);

		try {
			boolean acquired = mutex.acquire(waitTime, unit);

			if (acquired) {
				lockHolder.set(mutex);
			}

			return acquired;
		} catch (InterruptedException e) {
			log.error("[Zookeeper Lock] 락 획득 대기 중 인터럽트 발생. lockKey: {}", key, e);
			Thread.currentThread().interrupt();
			return false;
		} catch (Exception e) {
			log.error("[Zookeeper Lock] 락 획득 중 예기치 않은 오류 발생. lockKey: {}", key, e);
			throw e;
		}
	}

	@Override
	public void unlock(String key) {
		try {
			InterProcessMutex mutex = lockHolder.get();

			if (mutex != null && mutex.isAcquiredInThisProcess()) {
				mutex.release();
			} else {
				log.warn("[Zookeeper Lock] 현재 스레드가 보유하지 않은 락 해제 시도. lockKey: {}", key);
			}
		} catch (Exception e) {
			log.error("[Zookeeper Lock] 락 해제 중 예기치 않은 오류 발생. lockKey: {}", key, e);
		} finally {
			lockHolder.remove();
		}
	}

	@Override
	public LockType getLockType() {
		return LockType.ZOOKEEPER;
	}
}
