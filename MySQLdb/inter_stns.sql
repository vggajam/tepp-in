(select hops.train_no as tr, hops.stn_code as st,hops.hop_index as src_idx from hops where hops.stn_code = 'MUGR');


select src_stn, src_cnt from
(select distinct stations.stn_code as src_stn, stations.trains_cnt as src_cnt from hops as hp inner join (select hops.train_no as tr, hops.stn_code as st,hops.hop_index as src_idx from hops where hops.stn_code = 'NDLS')
as tb on hp.train_no= tb.tr, stations  where hp.hop_index > tb.src_idx  and stations.stn_code = hp.stn_code and trains_cnt > 39) as src_tbl,
(select distinct stations.stn_code as dst_stn, stations.trains_cnt as dst_cnt from hops as hp inner join (select hops.train_no as tr, hops.stn_code as st,hops.hop_index as src_idx from hops where hops.stn_code = 'MUGR')
as tb on hp.train_no= tb.tr, stations  where hp.hop_index < tb.src_idx  and stations.stn_code = hp.stn_code and trains_cnt > 39) dst_tbl where src_stn = dst_stn;