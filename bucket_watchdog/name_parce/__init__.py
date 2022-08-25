import copy
import itertools


def normal_spaces(key):
    for symb in "_#%$^:;,":
        key.replace(symb, " ")
    i = 0
    nk = ""
    while i < len(key):
        if key[i]==" ":
            if nk[-1]==" ":
                pass
            else:
                nk+=key[i]
        else:
            nk += key[i]
        i += 1
    if nk[0]==" ":
        nk = nk[1:]
    if nk[-1]==" ":
        nk = nk[:len(nk)-1]
    return nk


def remove_some(path, rmv=''):
    paths = path.split("/")
    paths.reverse()
    st = paths[0]
    contributer = paths[1]
    for symb in "-_#%$^:;,":
        st.replace(symb, " ")
    sst = [list(itertools.chain(*map(lambda x: x.split("."), s.split(" ")))) for s in st]
    print(sst)
    for ss in sst:
        print(ss)
        cnt = ss.count(rmv)
        if cnt > 0:
            for c in range(cnt):
                ss.remove(rmv)


        else:
            pass

    for si in sst:

        dtype = si.pop(-1)
        if 'этаж' in si:

            part = si.pop(si.index('этаж') - 1)
            print(part)
            si.remove('этаж')




        elif "arc" in si:
            part = 'arc'
        else:
            part = 'unknown'

        yield dict(
            floor=part,
            dtype=dtype,
            tags=si
        )
