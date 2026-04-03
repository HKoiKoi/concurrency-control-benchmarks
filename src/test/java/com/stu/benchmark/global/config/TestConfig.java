package com.stu.benchmark.global.config;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Bean;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.containers.wait.strategy.Wait;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

@Testcontainers
@TestConfiguration(proxyBeanMethods = false)
public class TestConfig {

	@Container
	public static GenericContainer<?> zookeeperContainer = new GenericContainer<>(
		DockerImageName.parse("zookeeper:3.9"))
		.withExposedPorts(2181)
		.waitingFor(Wait.forListeningPort());

	@DynamicPropertySource
	static void zookeeperProperties(DynamicPropertyRegistry registry) {
		zookeeperContainer.start();
		registry.add("zookeeper.host", zookeeperContainer::getHost);
		registry.add("zookeeper.port", () -> zookeeperContainer.getMappedPort(2181));
	}

	@Bean
	@ServiceConnection(name = "redis")
	public GenericContainer<?> redisContainer() {
		return new GenericContainer<>(DockerImageName.parse("redis:7.2-alpine"))
			.withExposedPorts(6379)
			.waitingFor(Wait.forListeningPort());
	}

	@Bean
	@ServiceConnection
	public MySQLContainer<?> mysqlContainer() {
		return new MySQLContainer<>("mysql:8.0")
			.withDatabaseName("test_db")
			.withUsername("test_user")
			.withPassword("testPass123!");
	}
}
