package com.stu.benchmark.global.lock;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum LockType {

	LETTUCE("lock:lettuce:course:"),
	;

	private final String prefix;

	public String generateKey(Long id) {
		return this.prefix + id;
	}
}
