package com.ssafy.edu.awesomeproject.domain.dummy.dto.request;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record DummyCreateUserRequest(@NotNull @Positive Integer generationNo) {}
