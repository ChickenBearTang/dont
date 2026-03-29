package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import jakarta.validation.constraints.NotBlank;


public record SaveBoxCreateRequest(@NotBlank String accountTypeUniqueNo) {}
