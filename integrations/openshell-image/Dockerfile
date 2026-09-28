FROM ubuntu:24.04@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3
COPY allowed.txt /work/allowed/fixture.txt
COPY denied.txt /work/denied/fixture.txt
RUN chmod 755 /work /work/allowed /work/denied && chmod 644 /work/allowed/fixture.txt /work/denied/fixture.txt
WORKDIR /tmp
CMD ["sleep", "infinity"]
