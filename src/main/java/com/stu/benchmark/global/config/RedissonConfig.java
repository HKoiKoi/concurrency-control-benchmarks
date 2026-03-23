package com.stu.benchmark.global.config;

import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.config.Config;
import org.springframework.boot.autoconfigure.data.redis.RedisConnectionDetails;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.util.StringUtils;

@Configuration
public class RedissonConfig {

	private static final String REDISSON_HOST_PREFIX = "redis://";

	@Bean
	public RedissonClient redissonClient(RedisConnectionDetails connectionDetails) {

		Config config = new Config();

		var standalone = connectionDetails.getStandalone();
		String address = REDISSON_HOST_PREFIX + standalone.getHost() + ":" + standalone.getPort();

		var singleServerConfig = config.useSingleServer()
			.setAddress(address)
			// 일반 명령 커넥션 풀
			.setConnectionMinimumIdleSize(32)
			.setConnectionPoolSize(64)
			// Pub-Sub 커넥션 풀
			.setSubscriptionConnectionMinimumIdleSize(10)
			.setSubscriptionConnectionPoolSize(50)
			// 타임아웃 설정
			.setConnectTimeout(3000)    // Redis 연결 시도 제한
			.setTimeout(3000)    // 명령 실행 결과 대기 시간
			.setRetryAttempts(3)    // 실패 시 재시도 횟수
			.setRetryInterval(1000);    // 재시도 간격

		if (StringUtils.hasText(connectionDetails.getPassword())) {
			singleServerConfig.setPassword(connectionDetails.getPassword());
		}

		return Redisson.create(config);
	}
}
