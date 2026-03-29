package com.ssafy.edu.awesomeproject.domain.dummy.client;

import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.request.FinanceMemberCreateRequest;
import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.response.FinanceMemberCreateResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.response.FinanceMemberSearchResponse;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.service.annotation.PostExchange;

public interface FinanceMemberClient {
    @PostExchange("/ssafy/api/v1/member")
    FinanceMemberCreateResponse createMember(@RequestBody FinanceMemberCreateRequest request);

    @PostExchange("/ssafy/api/v1/member/search")
    FinanceMemberSearchResponse searchMember(@RequestBody FinanceMemberCreateRequest request);

    @PostExchange("/ssafy/api/v1/member/inquire")
    FinanceMemberSearchResponse inquireMember(@RequestBody FinanceMemberCreateRequest request);
}
