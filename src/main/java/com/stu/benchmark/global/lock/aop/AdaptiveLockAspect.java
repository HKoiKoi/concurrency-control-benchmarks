package com.stu.benchmark.global.lock.aop;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import com.stu.benchmark.global.exception.LockAcquisitionException;
import com.stu.benchmark.global.lock.AdaptiveLockManager;
import com.stu.benchmark.global.lock.DistributedLock;
import com.stu.benchmark.global.lock.LockContextHolder;
import com.stu.benchmark.global.lock.LockType;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Aspect
@Order(1)
@Component
@RequiredArgsConstructor
public class AdaptiveLockAspect {

	private final AdaptiveLockManager adaptiveLockManager;

	// TODO: TPS 메트릭 수집하는 서비스 작성 필요

	@Around("@annotation(adaptiveLock)")
	public Object applyAdaptiveLock(ProceedingJoinPoint joinPoint, AdaptiveLock adaptiveLock) throws Throwable {

		MethodSignature signature = (MethodSignature)joinPoint.getSignature();

		Object dynamicKey = CustomSpELParser.getDynamicValue(
			signature.getParameterNames(),
			joinPoint.getArgs(),
			adaptiveLock.key()
		);

		// TODO: 현재 실시간 TPS 조회 로직 추가해야함.
		double currentTps = 40.0;    // 임시로 40 고정

		DistributedLock strategy = adaptiveLockManager.determineLockStrategy(currentTps);
		LockType lockType = strategy.getLockType();

		LockContextHolder.set(lockType);

		try {
			// 비관적 락은 별도 처리
			if (lockType == LockType.PESSIMISTIC) {
				log.debug("비관적 락 전략 실행. DB 쿼리 레벨에서 제어됩니다.");
				return joinPoint.proceed();
			}

			String lockKey = lockType.generateKey(dynamicKey);
			boolean acquired = strategy.tryLock(
				lockKey,
				adaptiveLock.waitTime(),
				adaptiveLock.leaseTime(),
				adaptiveLock.timeUnit()
			);

			if (!acquired) {
				log.error("[{}] 락 획득 타임아웃. key: {}", lockType, lockKey);
				throw new LockAcquisitionException("락 획득 대기 시간 초과");
			}

			try {
				return joinPoint.proceed();
			} finally {
				strategy.unlock(lockKey);
			}
		} finally {
			LockContextHolder.clear();
		}
	}
}
