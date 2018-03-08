
select *
from
(
select tr1.train_no tr1,hp1.stn_code src,hp1.dept_time sdt,hp2.arr_time iat,hp2.stn_code intr, (hp2.sday-hp1.day) as offset1 , tr2.train_no tr2,hp3.stn_code intr2,hp3.dept_time idt,hp4.arr_time dat,hp4.stn_code dst,(hp4.sday-hp3.day) as offset2,(hp2.sday-hp1.day+hp4.sday-hp3.day) as jdays,"sameday"
from 
	trains as tr1,
	(select * from hops) as hp1,
    (select * from hops) as hp2,
    trains as tr2,
    (select * from hops) as hp3,
    (select * from hops) as hp4 
where
tr1.train_no = hp1.train_no and
hp1.train_no = hp2.train_no and 
hp1.hop_index < hp2.hop_index and
hp1.stn_code = 'WL' and
tr2.train_no = hp3.train_no and
hp3.train_no = hp4.train_no and  
hp3.hop_index < hp4.hop_index and 
hp2.stn_code = hp3.stn_code and 
hp4.stn_code= 'OGL' and
tr1.train_no <> tr2.train_no and
tr1.jday & (1 << ((0-(hp1.sday-1) +7)%7)) > 0 and
tr2.jday & (1 << ((0+ hp3.day-1  +7)%7)) > 0 and 
hp2.arr_time < hp3.dept_time
union
select tr1.train_no tr1,hp1.stn_code src,hp1.dept_time sdt,hp2.arr_time iat,hp2.stn_code intr, (hp2.sday-hp1.day) as offset1 , tr2.train_no tr2,hp3.stn_code intr2,hp3.dept_time idt,hp4.arr_time dat,hp4.stn_code dst,(hp4.sday-hp3.day) as offset2,(hp2.sday-hp1.day+hp4.sday-hp3.day+1) as jdays,"nxtday"
from 
	trains as tr1,
	(select * from hops) as hp1,
    (select * from hops) as hp2,
    trains as tr2,
    (select * from hops) as hp3,
    (select * from hops) as hp4 
where
tr1.train_no = hp1.train_no and
hp1.train_no = hp2.train_no and 
hp1.hop_index < hp2.hop_index and
hp1.stn_code = 'WL' and
tr2.train_no = hp3.train_no and
hp3.train_no = hp4.train_no and  
hp3.hop_index < hp4.hop_index and 
hp2.stn_code = hp3.stn_code and 
hp4.stn_code= 'OGL' and
tr1.train_no <> tr2.train_no and
tr1.jday & (1 << ((0-(hp1.sday-1) +7)%7)) > 0 and
(tr2.jday & (1 << ((0+ hp3.day +7)%7)) > 0)
) as hip order by jdays;