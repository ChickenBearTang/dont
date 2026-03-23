package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.dto.response.EmailAvailabilityResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import java.util.Locale;
import org.springframework.stereotype.Service;

@Service
public class AccountValidationService {
    private final UserRepository userRepository;

    public AccountValidationService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public EmailAvailabilityResponseDto checkEmailAvailability(String email) {
        String normalizedEmail = email.trim().toLowerCase(Locale.ROOT);
        return new EmailAvailabilityResponseDto(
                normalizedEmail, !userRepository.existsByEmail(normalizedEmail));
    }
}
