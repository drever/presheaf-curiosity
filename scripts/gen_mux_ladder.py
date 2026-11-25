"""Generate N-to-1, 16-bit multiplexers in exactly the style of the Quip benchmarks mux32_16bit / mux64_16bit
(input shift registers z_sreg_1ton, select register z_regfile2, registered case statement), then synthesise them with
the same Yosys command as scripts/synth_quip.sh. Output: data/mux_ladder/muxN_16bit.v and data/quip_synth/ladder_muxN_16bit.json.
Usage: python scripts/gen_mux_ladder.py"""
import os, sys, shutil, subprocess
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
W = 16
def verilog(N):
    s = max(1, N.bit_length() - 1); name = f'mux{N}_16bit'
    v = [f"""module z_sreg_1ton (d, clk, q);
   parameter outwidth = {W};
   input clk;
   input d;
   output [outwidth-1:0] q;
   reg [outwidth-1:0] q;
   integer index;
   always @ (posedge clk)
     begin
	q[0] <= d;
	for (index=1; index<outwidth; index=index+1)
	  begin
	     q[index] <= q[index-1];
	  end
     end
endmodule

module z_regfile2 (d, clk, q);
   input [{s-1}:0] d;
   input clk;
   output [{s-1}:0] q;
   reg [{s-1}:0] q;
	always @ (posedge clk)
	begin
	   q = d;
	end
endmodule

module {name} (clk, sel, a, y);
   input clk;
   input [{s-1}:0] sel;
   input [{N-1}:0] a;
   output [{W-1}:0] y;
   reg [{W-1}:0] y;
   wire [{W-1}:0] {','.join(f'reg_a{i}' for i in range(N))};
   wire [{s-1}:0] reg_sel;
"""]
    v += [f"   z_sreg_1ton u{i} (.d(a[{i}]), .clk(clk), .q(reg_a{i}));" for i in range(N)]
    v += [f"\n   z_regfile2 u{N} (.d(sel), .clk(clk), .q(reg_sel));\n\n   always @(posedge clk)\n     begin\n\tcase(reg_sel)"]
    v += [f"\t  {i}: y <= reg_a{i};" for i in range(N)]
    v += ["\t  default: y <= reg_a0;\n\tendcase\n     end\nendmodule\n"]
    return name, '\n'.join(v)
if __name__ == '__main__':
    for N in (2, 4, 8, 16, 32, 64):
        name, src = verilog(N); f = os.path.join(ROOT, 'data', 'mux_ladder', name + '.v'); open(f, 'w').write(src)
        out = os.path.join(ROOT, 'data', 'quip_synth', f'ladder_{name}.json')
        subprocess.run([shutil.which('yowasp-yosys') or os.path.join(os.path.dirname(sys.executable), 'yowasp-yosys'), '-q', '-p', f'read_verilog {f}; synth -flatten -top {name}; write_json {out}'], check=True)
        print(name, 'done')
