package com.stu.benchmark.global.lock;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum LockType {

	PESSIMISTIC(""),

	LETTUCE("lock:lettuce:course:"),
	REDISSON("lock:redisson:course:"),

	ZOOKEEPER("/locks/zookeeper/course/"),
	;

	private final String prefix;

	/**
	 * 식별자(ID)를 받아 락 메커니즘에 맞는 Key 생성
	 * 비관적 락의 경우 prefix가 없으므로 ID 자체만 반환됨
	 */
	public String generateKey(Object id) {
		return this.prefix + id;
	}
}
