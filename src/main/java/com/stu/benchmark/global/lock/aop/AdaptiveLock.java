package com.stu.benchmark.global.lock.aop;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.util.concurrent.TimeUnit;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface AdaptiveLock {

	/**
	 * 락의 고유 키 (SpEL 표현식 사용)
	 */
	String key();

	/**
	 * 락 획득 대기 시간 (기본값: 5초)
	 */
	long waitTime() default 5000;

	/**
	 * 락 점유 유효 시간 (기본값: 3초)
	 */
	long leaseTime() default 3000;

	/**
	 * 시간 단위 (기본값: 밀리초)
	 */
	TimeUnit timeUnit() default TimeUnit.MILLISECONDS;
}
