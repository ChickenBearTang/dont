package com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.response;

import java.util.List;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StrictSecretaryResponse {
    private boolean is_approved;
    private String fact_violence_comment;
    private List<String> reasoning;
}
